"""면적 계수 c를 LS·LQ 격자로 훑는다 (후속실험 3 후속).

왜 하는가
--------
c=1은 "격자 칸끼리 독립"이라는 가정에서 나온 유도값인데, 실측 예측 편향이
LS +0.436 / LQ +0.256으로 둘 다 크게 과대추정이었다. c=0.5로 내리면
LS -0.097 / LQ -0.103으로 부호가 뒤집힌다. 즉 두 hazard 모두 최적 c가
0.5와 1 사이에 있다. 그 사이를 실제로 훑어 본다.

조건
----
a=1, b=0 고정이라 학습되는 prior 파라미터가 0개다(area_mode="grid").
따라서 A(1,1) · E(0.5,0.5) · G(1,0.5) · H(1,0.75)는 이 격자 위의 한 점과
정확히 같은 모형이고, 그 점들이 기존 결과와 맞는지로 스윕을 검증할 수 있다.

회귀·likelihood 파라미터 44개는 c마다 새로 학습한다. c가 prior를 바꾸면
posterior도 바뀌므로 다시 적합해야 한다.

쓰기
----
    python tools/sweep_c.py --c-ls 0.4 0.5 ... --c-lq 0.4 0.5 ... --lam 10
"""
from __future__ import annotations

import argparse
import itertools
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

import numpy as np
import pandas as pd
import torch

from eval import evaluate
from infer import infer
from loader import load_eval_ground_truth, load_pilot_a_batch
from marginal import marginalize
from prior import prior_log_w
from train import GT_PATH, STATS_PATH, USGS_PATH, to_eval_gt, to_eval_pred, train

OUT_DIR = REPO / "outputs" / "sweep_c"


def _bias(merged: pd.DataFrame, hazard: str) -> float:
    """평균 예측확률 − 실제 양성률. 양수면 과대예측이다."""
    rows = merged[merged[f"{hazard}_eval_mask"].astype(bool)]
    return float(rows[f"p_{hazard}"].mean() - rows[f"{hazard}_true"].mean())


def run_point(batch, eval_gt, gt_df, *, c_ls, c_lq, lam, epochs, seed):
    reg, like, pri, hist = train(
        batch, seed=seed, epochs=epochs, lam_gamma=lam,
        area_mode="grid", c_ls=c_ls, c_lq=c_lq,
    )
    with torch.no_grad():
        out_r = reg(batch)
        out_l = like(batch, out_r.mu)
        log_joint, log_Py = marginalize(prior_log_w(pri, batch), out_l.log_L)
        p_ls, p_lq = infer(log_joint, log_Py)

    r = evaluate(gt_df, to_eval_pred(batch, p_ls, p_lq, eval_gt, pri=pri))

    # 행별 예측을 남겨 둔다. 정답 규칙이 바뀌어도 다시 학습하지 않고 채점만 다시 할 수 있다.
    (OUT_DIR / "pred").mkdir(parents=True, exist_ok=True)
    r.merged.sort_values(["event_idx", "muni_code"]).to_csv(
        OUT_DIR / "pred" / f"detail_cls{c_ls}_clq{c_lq}.csv", index=False, encoding="utf-8-sig")

    return {
        "c_ls": c_ls, "c_lq": c_lq, "lam_gamma": lam,
        "ls_prior": r.auc_zprior_ls_wavg, "ls_post": r.auc_ls_wavg,
        "ls_gain": r.auc_ls_wavg - r.auc_zprior_ls_wavg,
        "lq_prior": r.auc_zprior_lq_wavg, "lq_post": r.auc_lq_wavg,
        "lq_gain": r.auc_lq_wavg - r.auc_zprior_lq_wavg,
        "mse_ls": r.mse_ls, "mse_lq": r.mse_lq,
        "bias_ls": _bias(r.merged, "ls"), "bias_lq": _bias(r.merged, "lq"),
        # hist는 DataFrame이다. 마지막 epoch의 NLL을 조건 간 비교용으로 남긴다.
        "nll": float(hist["nll_total"].iloc[-1]) if len(hist) else np.nan,
        "n_ls": r.n_ls, "n_lq": r.n_lq,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--c-ls", nargs="+", type=float, required=True)
    ap.add_argument("--c-lq", nargs="+", type=float, required=True)
    ap.add_argument("--lam", type=float, default=10.0)
    ap.add_argument("--epochs", type=int, default=3000)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", default="sweep_c.csv")
    a = ap.parse_args()

    batch = load_pilot_a_batch(STATS_PATH, USGS_PATH)
    eval_gt = load_eval_ground_truth(GT_PATH, batch)
    gt_df = to_eval_gt(eval_gt)

    grid = list(itertools.product(a.c_ls, a.c_lq))
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_csv = OUT_DIR / a.out
    print(f"격자 {len(grid)}점 x {a.epochs}에폭 / lam_gamma={a.lam}")

    rows, t0 = [], time.time()
    for i, (c_ls, c_lq) in enumerate(grid, 1):
        t = time.time()
        rows.append(run_point(batch, eval_gt, gt_df, c_ls=c_ls, c_lq=c_lq,
                              lam=a.lam, epochs=a.epochs, seed=a.seed))
        # 중간에 끊겨도 여기까지는 남는다.
        pd.DataFrame(rows).to_csv(out_csv, index=False, encoding="utf-8-sig")
        done, took = time.time() - t0, time.time() - t
        print(f"[{i}/{len(grid)}] c_LS={c_ls} c_LQ={c_lq}  {took:.0f}초  "
              f"누적 {done/60:.1f}분  남은 예상 {(done/i)*(len(grid)-i)/60:.1f}분", flush=True)

    print(f"\n저장: {out_csv}  ({len(rows)}행)")


if __name__ == "__main__":
    main()
