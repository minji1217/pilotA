"""교수님 요청(2026-11-15): 학습은 그대로, 테스트할 때만 평가 지진의 cov 항을 0으로(log cov = 0, 즉 cov = 1) 두고 산사태 정확도 확인.

- 학습: AdminDER 최종 설정 그대로 (λ_γ = λ_κ = 10, 3000 에폭, 산사태 라벨 학습, 액상화 라벨 미사용, LQ b-only).
  평가 지진의 행은 학습에서 통째로 빠지므로 평가 지진의 cov는 원래도 학습에 안 들어간다 → 학습은 기존과 완전히 같다.
  저장된 모델이 없어 다시 학습하지만 결정적(초기값 상수·전체 배치)이라 기존 모델과 같다. 아래에서 기존 AUC 재현을 assert로 확인.
- 테스트: 평가 지진 행의 log_cov_ls만 0으로 바꾼 batch로 prior·사후·α_e 맞춤을 다시 계산 (report_holdout 그대로 사용).
  학습 지진 행의 cov는 건드리지 않는다(α_e 맞춤은 평가 지진 행만 씀).

실행 (repo 폴더에서): python cov0_loeo.py <d9|d5> <지진 이름...>
  d9 = ① 9개 지진 LOEO(8개 학습), 기준 holdout_summary_rq4nl_full_*
  d5 = ② DPM 5개 LOEO(4개 학습), 기준 holdout_summary_rq4d5_full_*
결과: outputs/holdout_summary_cov0_<d9|d5>_<지진>.csv (+detail). 재현 확인용 원래 cov 채점은 _cov0ref_ 꼬리표.
"""
import dataclasses
import sys
import time

import numpy as np
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

torch.set_num_threads(2)
mode, events = sys.argv[1], sys.argv[2:]
REF = {"d9": "rq4nl_full", "d5": "rq4d5_full"}[mode]
DPM5 = ["2016 구마모토", "2018 오사카", "2018 훗카이도", "2021 후쿠시마", "2024 노토반도"]

batch = load_pilot_a_batch(STATS_PATH, USGS_PATH)
batch = attach_ls_labels(GT_PATH, batch, load_eval_ground_truth(GT_PATH, batch))
assert batch.batch_size == 418
in_dpm5 = torch.isin(batch.event_idx, torch.tensor([EVENT_TO_INDEX[e] for e in DPM5]))


def score(b, reg, like, pri, ev, sfx):
    with torch.no_grad():
        out_r = reg(b)
        log_joint, log_Py = marginalize(prior_log_w(pri, b), like(b, out_r.mu).log_L)
        p_ls, p_lq = infer(log_joint, log_Py)
    report_holdout(b, reg, like, pri, p_ls, p_lq, ev, sfx)
    return pd.read_csv(f"{REPO}/outputs/holdout_summary{sfx}.csv").iloc[0]


for ev in events:
    t0 = time.time()
    ho = EVENT_TO_INDEX[ev]
    keep = (batch.event_idx != ho) & (in_dpm5 if mode == "d5" else True)
    reg, like, pri, hist = train(
        batch=subset_batch(batch, keep), seed=0, epochs=3000, lr=0.02, lam_gamma=10.0,
        area_mode="fixed-cov-mtn", lam_kappa=10.0, mtn_standardize="train",
        reg_mtn=False, lq_mtn=False, lq_b_only=True, use_labels=True, lq_labels=False,
    )
    name = ev.replace(" ", "")

    # 1) 원래 cov로 채점 → 기존 결과와 같아야 함 (같은 모델인지 확인)
    s_ref = score(batch, reg, like, pri, ev, f"_cov0ref_{mode}_{name}")
    old = pd.read_csv(f"{REPO}/outputs/holdout_summary_{REF}_{name}.csv").iloc[0]
    for c in ["auc_A_own_prior", "auc_cov_kappa_prior", "auc_posterior_alpha_fit", "auc_lq_posterior_alpha_fit"]:
        assert np.isclose(s_ref[c], old[c], atol=1e-9, equal_nan=True), (ev, c, s_ref[c], old[c])

    # 2) 평가 지진 행만 log cov = 0
    lc = batch.log_cov_ls.clone()
    n_changed = int(((batch.event_idx == ho) & (lc != 0)).sum())
    lc[batch.event_idx == ho] = 0.0
    s0 = score(dataclasses.replace(batch, log_cov_ls=lc), reg, like, pri, ev, f"_cov0_{mode}_{name}")
    print(f"[{mode}] {ev}  cov 바뀐 행 {n_changed}  LS 사후 {s_ref['auc_posterior_alpha_fit']:.4f} → {s0['auc_posterior_alpha_fit']:.4f}"
          f"  prior(cov+κ) {s_ref['auc_cov_kappa_prior']:.4f} → {s0['auc_cov_kappa_prior']:.4f}  {time.time() - t0:.0f}s", flush=True)
