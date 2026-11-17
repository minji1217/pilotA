"""RQ4 ablation, dpm5 판: DPM 있는 5개 지진 안에서만 LOEO 5폴드 (평가 지진 빼고 나머지 4개로 학습).
언니 run_ablation.py --dpm5와 같은 설계. 나머지 설정은 rq4_run_nolq.py(최종 설정)와 같다.

repo 코드는 바꾸지 않고 train.train()의 ablation 인자(작업 트리의 미커밋 변경)만 쓴다.
설정은 TRACE 최종 = followup4-lq-J-nolabels 기본값(언니 README의 A2): area_mode=fixed-cov-mtn,
lam_gamma=10, lam_kappa=10, 산사태 라벨 학습 + 액상화 라벨 미사용, LQ b-only, epochs 3000, lr 0.02, seed 0.
(작업 트리는 labels 브랜치지만 train()에 lq_labels=False를 직접 넘기므로 nolabels 브랜치와 같은 모델이다.
 두 브랜치의 코드 차이는 train.py DEFAULT_LQ_LABELS 한 줄뿐.)

조건
  full     : TRACE 전체 (10월 nolabels 결과 holdout_summary_lqJnl_* 재현용)
  uniform  : 입력 층위 — prior를 균등(z=0)으로
  nopgv    : 입력 층위 — beta_c·log PGV 항 제거
  poisson  : 구조 층위 — 음이항 → 포아송
  noexp    : 구조 층위 — 노출 offset 제거 (mu = lambda)
  single   : 학습 층위 — 평가 이벤트 하나의 피해만으로 단독 학습 (그 이벤트 라벨은 누수라 미사용)

실행: (repo 폴더에서) python <이 파일> <조건>
"""
import sys
import time

REPO = r"C:\Users\PC\Desktop\pilotA"
sys.path.insert(0, REPO)

import torch

from train import (GT_PATH, STATS_PATH, USGS_PATH, DEFAULT_AREA_MODE, DEFAULT_LQ_B_ONLY,
                   DEFAULT_LQ_LABELS, report_holdout, train)
from loader import attach_ls_labels, load_eval_ground_truth, load_pilot_a_batch, subset_batch
from marginal import marginalize
from infer import infer
from prior import prior_log_w
from schema import EVENTS, EVENT_TO_INDEX

COND = {
    "full": {},
    "uniform": dict(prior_uniform=True),
    "nopgv": dict(use_pgv=False),
    "poisson": dict(like_dist="poisson"),
    "noexp": dict(use_exposure=False),
    "single": {},
}

cond = sys.argv[1]
assert cond in COND, cond
assert DEFAULT_AREA_MODE == "fixed-cov-mtn" and DEFAULT_LQ_B_ONLY  # LQ 라벨은 아래에서 직접 끈다

batch = load_pilot_a_batch(STATS_PATH, USGS_PATH)
eval_gt = load_eval_ground_truth(GT_PATH, batch)
batch = attach_ls_labels(GT_PATH, batch, eval_gt)

DPM5 = ["2016 구마모토", "2018 오사카", "2018 훗카이도", "2021 후쿠시마", "2024 노토반도"]
in_dpm5 = torch.isin(batch.event_idx, torch.tensor([EVENT_TO_INDEX[e] for e in DPM5]))

for ev in DPM5:
    t0 = time.time()
    ho = EVENT_TO_INDEX[ev]
    if cond == "single":
        tb = subset_batch(batch, batch.event_idx == ho)
        labels = dict(use_labels=False, lq_labels=False)
    else:
        tb = subset_batch(batch, in_dpm5 & (batch.event_idx != ho))
        labels = dict(use_labels=True, lq_labels=False)  # 언니 설정(nolabels 브랜치)
    reg, like, pri, hist = train(
        batch=tb, seed=0, epochs=3000, lr=0.02, lam_gamma=10.0,
        area_mode="fixed-cov-mtn", lam_kappa=10.0, mtn_standardize="train",
        reg_mtn=False, lq_mtn=False, lq_b_only=True, **labels, **COND[cond],
    )
    with torch.no_grad():
        out_r = reg(batch)
        out_l = like(batch, out_r.mu)
        log_joint, log_Py = marginalize(prior_log_w(pri, batch), out_l.log_L)
        p_ls, p_lq = infer(log_joint, log_Py)
    sfx = f"_rq4d5_{cond}_{ev.replace(' ', '')}"
    report_holdout(batch, reg, like, pri, p_ls, p_lq, ev, sfx)
    hist.to_csv(f"outputs/rq4/dpm5/loss_{cond}_{ev.replace(' ', '')}.csv", index=False)
    print(f"[{cond}] {ev} 학습행 {tb.batch_size} 끝 {time.time() - t0:.0f}s  최종 nll/행 {hist.nll_per_row.iloc[-1]:.4f}", flush=True)
