"""에폭 수만 바꿔 AdminDER 최종 설정 LOEO를 다시 돈다 (3000 에폭 미수렴 확인용, 엑셀에는 넣지 않음).

설정은 rq4nl full과 같음: λ_γ = λ_κ = 10, 산사태 라벨 학습, 액상화 라벨 미사용, LQ b-only, 평가 지진 빼고 학습.
결과: outputs/holdout_summary_ep<에폭>_<지진>.csv (+detail), outputs/rq3/gamma_ep<에폭>_<지진>.csv, loss는 outputs/rq3/loss_ep<에폭>_<지진>.csv
실행: (repo 폴더에서) python ep_loeo.py <에폭> <지진 이름...>
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
from schema import CHANNELS, EVENT_TO_INDEX

ep = int(sys.argv[1])
events = sys.argv[2:]
tag = f"ep{ep}"
out = Path(REPO) / "outputs" / "rq3"
out.mkdir(parents=True, exist_ok=True)

batch = load_pilot_a_batch(STATS_PATH, USGS_PATH)
batch = attach_ls_labels(GT_PATH, batch, load_eval_ground_truth(GT_PATH, batch))
for ev in events:
    t0 = time.time()
    ho = EVENT_TO_INDEX[ev]
    reg, like, pri, hist = train(
        batch=subset_batch(batch, batch.event_idx != ho), seed=0, epochs=ep, lr=0.02, lam_gamma=10.0,
        area_mode="fixed-cov-mtn", lam_kappa=10.0, mtn_standardize="train",
        reg_mtn=False, lq_mtn=False, lq_b_only=True, use_labels=True, lq_labels=False,
    )
    with torch.no_grad():
        out_r = reg(batch)
        out_l = like(batch, out_r.mu)
        log_joint, log_Py = marginalize(prior_log_w(pri, batch), out_l.log_L)
        p_ls, p_lq = infer(log_joint, log_Py)
    name = ev.replace(" ", "")
    report_holdout(batch, reg, like, pri, p_ls, p_lq, ev, f"_{tag}_{name}")
    pd.DataFrame({"channel": CHANNELS, "gamma_ls": reg.gamma_ls.detach().numpy(),
                  "gamma_lq": reg.gamma_lq.detach().numpy()}).to_csv(out / f"gamma_{tag}_{name}.csv", index=False)
    hist.to_csv(out / f"loss_{tag}_{name}.csv", index=False)
    print(f"[{tag}] {ev} 끝 {time.time() - t0:.0f}s", flush=True)
