"""교수님 요청(2026-11-15) A안: ② 설정 그대로, DPM 5개 지진 '전부'로 한 번 학습한 모델로 2000 돗토리·2004 니가타현주에쓰를 평가.

- 모델·설정은 ②(rq4d5_full)와 같음: λ_γ = λ_κ = 10, 3000 에폭, lr 0.02, seed 0, 산사태 라벨 학습, 액상화 라벨 미사용, LQ b-only.
- 학습 = DPM 5개(구마모토·오사카·훗카이도·후쿠시마·노토) 전부. 두 평가 지진은 학습에 없음 → LOEO와 같은 조건.
- 평가 = report_holdout 그대로(평가 지진 α_e 하나만 그 지진 피해로 맞춘 사후, 라벨 미사용).
  표 3과 맞추려고 평가 지진 cov = 1 채점도 같이 냄(돗토리는 원래 cov 없음).
결과: outputs/holdout_summary_d5all_<지진>.csv, outputs/holdout_summary_d5all_cov0_<지진>.csv (+detail)
"""
import dataclasses
import sys

import pandas as pd
import torch

REPO = r"C:\Users\PC\Desktop\pilotA"
sys.path.insert(0, REPO)
sys.stdout.reconfigure(encoding="utf-8")

from train import GT_PATH, STATS_PATH, USGS_PATH, report_holdout, train
from loader import attach_ls_labels, load_eval_ground_truth, load_pilot_a_batch, subset_batch
from marginal import marginalize
from infer import infer
from prior import prior_log_w
from schema import EVENT_TO_INDEX

torch.set_num_threads(4)
DPM5 = ["2016 구마모토", "2018 오사카", "2018 훗카이도", "2021 후쿠시마", "2024 노토반도"]
EVAL = ["2000 돗토리", "2004 니가타현주에쓰"]

batch = load_pilot_a_batch(STATS_PATH, USGS_PATH)
batch = attach_ls_labels(GT_PATH, batch, load_eval_ground_truth(GT_PATH, batch))
assert batch.batch_size == 418
in_dpm5 = torch.isin(batch.event_idx, torch.tensor([EVENT_TO_INDEX[e] for e in DPM5]))
tb = subset_batch(batch, in_dpm5)
for e in EVAL:
    assert not (tb.event_idx == EVENT_TO_INDEX[e]).any()

reg, like, pri, hist = train(
    batch=tb, seed=0, epochs=3000, lr=0.02, lam_gamma=10.0,
    area_mode="fixed-cov-mtn", lam_kappa=10.0, mtn_standardize="train",
    reg_mtn=False, lq_mtn=False, lq_b_only=True, use_labels=True, lq_labels=False,
)
print(f"학습 {tb.batch_size}행, 최종 손실 {float(hist.loss_total.iloc[-1]):.2f}, κ {float(pri.kappa):+.4f}", flush=True)


def score(b, ev, sfx):
    with torch.no_grad():
        log_joint, log_Py = marginalize(prior_log_w(pri, b), like(b, reg(b).mu).log_L)
        p_ls, p_lq = infer(log_joint, log_Py)
    report_holdout(b, reg, like, pri, p_ls, p_lq, ev, sfx)
    return pd.read_csv(f"{REPO}/outputs/holdout_summary{sfx}.csv").iloc[0]


for ev in EVAL:
    name = ev.replace(" ", "")
    s = score(batch, ev, f"_d5all_{name}")
    lc = batch.log_cov_ls.clone()
    lc[batch.event_idx == EVENT_TO_INDEX[ev]] = 0.0
    s0 = score(dataclasses.replace(batch, log_cov_ls=lc), ev, f"_d5all_cov0_{name}")
    print(f"{ev}  LS n={s.n} ({s.n_pos}/{s.n_neg})  USGS {s.auc_usgs_prior:.4f}  변환 {s.auc_A_own_prior:.4f}  "
          f"prior+cov+κ {s.auc_cov_kappa_prior:.4f} (cov=1 {s0.auc_cov_kappa_prior:.4f})  "
          f"사후 {s.auc_posterior_alpha_fit:.4f} (cov=1 {s0.auc_posterior_alpha_fit:.4f})", flush=True)
    print(f"{'':>14}LQ n={s.n_lq} ({s.n_pos_lq}/{s.n_neg_lq})  USGS {s.auc_lq_usgs_prior:.4f}  변환 {s.auc_lq_A_own_prior:.4f}  "
          f"사후 {s.auc_lq_posterior_alpha_fit:.4f}", flush=True)
