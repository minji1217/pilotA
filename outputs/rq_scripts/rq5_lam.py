"""RQ5 (i): λ_γ 민감도. TRACE 최종 설정(rq4nl full과 같은 학습 호출)에서 λ_γ만 바꾼다.

λ_κ는 10으로 고정(최종 설정과 같음) — 한 번에 하나만 바꾸려고.
λ_γ = 10은 rq4nl_full 결과를 그대로 쓴다.
결과: outputs/holdout_summary_rq5l<λ>_*.csv (+detail), outputs/rq5/gamma_lam<λ>.csv (폴드별 γ)

실행: (repo 폴더에서) python rq5_lam.py <λ_γ>
"""
import sys
import time
from pathlib import Path

REPO = r"C:\Users\PC\Desktop\pilotA"
sys.path.insert(0, REPO)
sys.stdout.reconfigure(encoding="utf-8")

import pandas as pd
import torch

from train import GT_PATH, STATS_PATH, USGS_PATH, report_holdout, train
from loader import attach_ls_labels, load_eval_ground_truth, load_pilot_a_batch, subset_batch
from marginal import marginalize
from infer import infer
from prior import prior_log_w
from schema import CHANNELS, EVENTS, EVENT_TO_INDEX

lam = float(sys.argv[1])
tag = f"rq5l{sys.argv[1]}"
OUT = Path(REPO) / "outputs" / "rq5"
OUT.mkdir(parents=True, exist_ok=True)

batch = load_pilot_a_batch(STATS_PATH, USGS_PATH)
batch = attach_ls_labels(GT_PATH, batch, load_eval_ground_truth(GT_PATH, batch))

rows = []
for ev in EVENTS:
    t0 = time.time()
    ho = EVENT_TO_INDEX[ev]
    reg, like, pri, hist = train(
        batch=subset_batch(batch, batch.event_idx != ho), seed=0, epochs=3000, lr=0.02, lam_gamma=lam,
        area_mode="fixed-cov-mtn", lam_kappa=10.0, mtn_standardize="train",
        reg_mtn=False, lq_mtn=False, lq_b_only=True, use_labels=True, lq_labels=False,
    )
    with torch.no_grad():
        out_r = reg(batch)
        out_l = like(batch, out_r.mu)
        log_joint, log_Py = marginalize(prior_log_w(pri, batch), out_l.log_L)
        p_ls, p_lq = infer(log_joint, log_Py)
    report_holdout(batch, reg, like, pri, p_ls, p_lq, ev, f"_{tag}_{ev.replace(' ', '')}")
    g_ls, g_lq = reg.gamma_ls.detach().tolist(), reg.gamma_lq.detach().tolist()
    for c, a, b in zip(CHANNELS, g_ls, g_lq):
        rows.append({"fold": ev, "channel": c, "gamma_ls": a, "gamma_lq": b})
    print(f"[λ_γ={lam}] {ev} 끝 {time.time() - t0:.0f}s  b_LQ {float(pri.b_value[1]):.3f}", flush=True)

pd.DataFrame(rows).to_csv(OUT / f"gamma_lam{sys.argv[1]}.csv", index=False, encoding="utf-8-sig")
