"""
Pilot A - experiment.py

과확신(posterior가 0/1로 쏠리는 현상)을 줄이기 위한 두 가지 제약을
조합해 돌리고 결과를 한 장의 CSV로 모은다.

축 1) Prior a, b 제약        free / fixed / bounded   (prior.py 참고)
축 2) gamma L2 정규화 계수    lam_gamma = 0, 0.1, 1, 10

lam_gamma=0 + mode=free 가 현재 상태이므로 그 행이 기준선이다.

판단 기준은 MSE 하나가 아니라 "상수만 찍는 베이스라인을 넘었는가"이다.
넘지 못하면 모델이 데이터를 활용하지 못하고 있다는 뜻이므로
베이스라인 두 개를 같은 CSV 아래쪽에 함께 적는다.

실행:
    python experiment.py
"""
from pathlib import Path

import numpy as np
import pandas as pd
import torch

from eval import evaluate
from infer import infer
from loader import load_eval_ground_truth, load_pilot_a_batch
from marginal import marginalize
from reporting import GROUP_ORDER, dump_params
from train import GT_PATH, STATS_PATH, USGS_PATH, to_eval_gt, to_eval_pred, train

PRIOR_MODES = ("free", "fixed", "bounded")
LAM_GAMMAS = (0.0, 0.1, 1.0, 10.0)

# 후속실험에서 채택된 조건을 이름으로 고정해 둔다.
# 매번 --modes/--lams를 손으로 넣으면 조건이 조용히 어긋난다.
#
# followup1 : P2(a,b 범위제한) + lam_gamma=10 에 취약성 공변량 2개(delta_c, eta_c)를
#             더한 조건. 공변량 추가 자체는 regression.py에 들어가 있으므로
#             러너 쪽에서는 prior/정규화 조건만 지정하면 된다.
# followup2 : LQ prior를 최대집계로 바꾸고 b 범위를 [-2, 4]로 넓힌 조건.
#             prior 집계 방식 전환은 loader 쪽(followup2-prior 브랜치) 작업이라
#             여기서는 b 범위만 잡아 둔다.
PRESETS = {
    "followup1": {"modes": ("bounded",), "lams": (10.0,), "b_bound": 2.0},
    "followup2": {"modes": ("bounded",), "lams": (10.0,), "b_bound": 4.0},
}

# 완료기준의 주 지표가 "2004 니가타 LS posterior AUC"라 이벤트 번호를 고정해 둔다.
# schema.EVENTS의 0번이 2004 니가타현주에쓰다.
MAIN_EVENT_IDX = 0

OUT_DIR = Path("outputs")
RUN_DIR = OUT_DIR / "experiments"

# bounded 모드에서 b가 상한 2.0에 계속 붙어 나왔다.
# 제약이 물린 상태라 최적값을 찾은 게 아니라 잘라낸 것이므로
# 범위를 넓혀 안쪽에서 멈추는지 확인할 수 있게 해둔다.
DEFAULT_B_BOUND = 2.0


def run_one(batch, eval_gt, gt_df, *, mode, lam, epochs, seed, b_bound=DEFAULT_B_BOUND):
    """한 조합을 학습하고 평가 결과 한 행을 만든다."""
    tag = f"{mode}_lam{lam:g}"
    print(f"\n{'='*60}\n[{tag}] prior={mode}  lam_gamma={lam}\n{'='*60}")

    reg, like, pri, hist = train(
        batch, seed=seed, epochs=epochs, lam_gamma=lam,
        prior_mode=mode, b_bound=b_bound,
    )

    with torch.no_grad():
        out_r = reg(batch)
        out_l = like(batch, out_r.mu)
        log_w = pri(batch.pi_ls, batch.pi_lq)
        log_joint, log_Py = marginalize(log_w, out_l.log_L)
        p_ls, p_lq = infer(log_joint, log_Py)

    result = evaluate(gt_df, to_eval_pred(batch, p_ls, p_lq, eval_gt))

    RUN_DIR.mkdir(parents=True, exist_ok=True)
    dump_params(reg, like, pri, path=str(RUN_DIR / f"params_{tag}.csv"))
    result.per_event.to_csv(
        RUN_DIR / f"eval_per_event_{tag}.csv", index=False, encoding="utf-8-sig"
    )
    result.merged.sort_values(["event_idx", "muni_code"]).to_csv(
        RUN_DIR / f"eval_detail_{tag}.csv", index=False, encoding="utf-8-sig"
    )

    pd.DataFrame({
        "event_idx": batch.event_idx.tolist(),
        "muni_code": list(batch.municipality_code),
        "p_ls": p_ls.numpy(),
        "p_lq": p_lq.numpy(),
    }).to_csv(RUN_DIR / f"predictions_{tag}.csv", index=False, encoding="utf-8-sig")

    with torch.no_grad():
        a, b = pri.a_value.detach(), pri.b_value.detach()
        g_ls, g_lq = reg.gamma_ls.detach(), reg.gamma_lq.detach()
        sum_g2 = float((g_ls ** 2).sum() + (g_lq ** 2).sum())

        # 과확신 정도: 예측이 0/1 끝에 몰려 있을수록 커진다.
        p_all = torch.cat([p_ls, p_lq]).numpy()
        middle = float(((p_all > 0.1) & (p_all < 0.9)).mean())

    # 완료기준 주 지표. 해당 이벤트가 평가 대상에 없으면 nan으로 둔다.
    main_rows = result.per_event.loc[result.per_event["event_idx"] == MAIN_EVENT_IDX]
    main_auc_ls = float(main_rows["auc_ls"].iloc[0]) if len(main_rows) else float("nan")
    main_auc_prior_ls = (
        float(main_rows["auc_prior_ls"].iloc[0]) if len(main_rows) else float("nan")
    )

    return {
        "prior_mode": mode,
        "lam_gamma": lam,
        "b_bound": b_bound if mode == "bounded" else np.nan,
        "mse_ls": result.mse_ls,
        "mse_lq": result.mse_lq,
        # 후속실험 1의 완료기준. posterior AUC가 prior 단독 AUC를 넘어야 한다.
        "auc_ls": result.auc_ls,
        "auc_lq": result.auc_lq,
        "auc_prior_ls": result.auc_prior_ls,
        "auc_prior_lq": result.auc_prior_lq,
        "auc_ls_wavg": result.auc_ls_wavg,
        "auc_lq_wavg": result.auc_lq_wavg,
        "auc_prior_ls_wavg": result.auc_prior_ls_wavg,
        "auc_prior_lq_wavg": result.auc_prior_lq_wavg,
        # 주 기준: 2004 니가타 LS
        "auc_ls_niigata2004": main_auc_ls,
        "auc_prior_ls_niigata2004": main_auc_prior_ls,
        "n_ls": result.n_ls,
        "n_lq": result.n_lq,
        "n": result.n,
        "a_LS": float(a[0]), "b_LS": float(b[0]),
        "a_LQ": float(a[1]), "b_LQ": float(b[1]),
        "gamma_ls_max": float(g_ls.max()),
        "gamma_lq_max": float(g_lq.max()),
        "sum_gamma2": sum_g2,
        # 과확신 지표. 0.1~0.9 사이 예측의 비율이며 높을수록 확률다운 예측이다.
        # MSE만으로는 "정규화가 과확신을 실제로 풀었는가"를 볼 수 없어 함께 남긴다.
        "frac_middle": middle,
    }


def baseline_rows(gt_df):
    """모델을 전혀 쓰지 않는 기준선. 이걸 못 넘으면 학습이 의미 없다."""
    # 모델과 같은 행에서 재야 비교가 성립하므로 베이스라인도 각자의 mask로 자른다.
    ls = gt_df.loc[gt_df["ls_eval_mask"].astype(bool), "ls_true"].to_numpy(float)
    lq = gt_df.loc[gt_df["lq_eval_mask"].astype(bool), "lq_true"].to_numpy(float)

    def pair(name, p_ls_const, p_lq_const):
        return {
            "prior_mode": name, "lam_gamma": np.nan,
            "mse_ls": float(np.mean((ls - p_ls_const) ** 2)),
            "mse_lq": float(np.mean((lq - p_lq_const) ** 2)),
            "n_ls": len(ls), "n_lq": len(lq), "n": len(gt_df),
        }

    return [
        pair("[베이스라인] 전부 0.5", 0.5, 0.5),
        pair("[베이스라인] 전부 기저확률", ls.mean(), lq.mean()),
    ]


def collect_params(out_path=None, tags=None):
    """조합별 params_*.csv를 한 장으로 합친다.

    파일을 따로 보내면 비교가 안 되므로
    파라미터를 행, 조합을 열로 두고 value만 모은다.

    tags를 주면 그 조합만 모은다.
    공변량 추가 전(43행)과 추가 후(55행) 실행분을 한 장에 섞으면
    없는 칸이 전부 빈값이 되고, 이벤트명 표기가 바뀐 경우 같은 파라미터가
    두 행으로 갈라져 표가 무너진다. 이번 실행분만 볼 때 쓴다.
    """
    files = sorted(RUN_DIR.glob("params_*.csv"))
    if tags is not None:
        wanted = {f"params_{t}.csv" for t in tags}
        files = [f for f in files if f.name in wanted]
    if not files:
        raise FileNotFoundError(f"{RUN_DIR}에 params_*.csv가 없습니다. 먼저 실험을 돌리세요.")

    frames = []
    for f in files:
        tag = f.stem.replace("params_", "")
        df = pd.read_csv(f)[["group", "idx", "label", "value"]]
        frames.append(
            df.rename(columns={"value": tag}).set_index(["group", "idx", "label"])
        )

    merged = pd.concat(frames, axis=1).reset_index()
    merged = merged.sort_values(
        ["group", "idx"],
        key=lambda col: col.map({g: i for i, g in enumerate(GROUP_ORDER)})
        if col.name == "group" else col,
    ).reset_index(drop=True)

    out_path = Path(out_path or OUT_DIR / "params_comparison.csv")
    merged.to_csv(out_path, index=False, encoding="utf-8-sig")
    print(f"저장: {out_path}  ({len(merged)}행 x 조합 {len(files)}개)")
    return merged


def main(*, epochs=3000, seed=0, modes=PRIOR_MODES, lams=LAM_GAMMAS,
         b_bound=DEFAULT_B_BOUND, out_name="experiments.csv"):
    batch = load_pilot_a_batch(STATS_PATH, USGS_PATH)
    eval_gt = load_eval_ground_truth(GT_PATH, batch)
    gt_df = to_eval_gt(eval_gt)
    out_csv = OUT_DIR / out_name

    n_ev = int(eval_gt.event_idx.unique().numel())
    print(f"batch {batch.batch_size}행 / 평가 GT {eval_gt.batch_size}행 / 이벤트 {n_ev}개")
    print(f"조합 {len(modes) * len(lams)}개 x {epochs}에폭 (bounded의 b 범위 ±{b_bound})")

    rows, tags = [], []
    for mode in modes:
        for lam in lams:
            tags.append(f"{mode}_lam{lam:g}")
            rows.append(run_one(batch, eval_gt, gt_df, mode=mode, lam=lam,
                                epochs=epochs, seed=seed, b_bound=b_bound))
            # 중간에 끊겨도 여기까지 결과는 남는다.
            pd.DataFrame(rows).to_csv(out_csv, index=False, encoding="utf-8-sig")

    df = pd.concat([pd.DataFrame(rows), pd.DataFrame(baseline_rows(gt_df))],
                   ignore_index=True)
    df.to_csv(out_csv, index=False, encoding="utf-8-sig")

    print()
    print("=" * 60)
    print(f"저장: {out_csv} ({len(df)}행)")
    show = ["prior_mode", "lam_gamma", "mse_ls", "mse_lq",
            "auc_ls", "auc_prior_ls", "auc_lq", "auc_prior_lq",
            "auc_ls_niigata2004", "sum_gamma2", "frac_middle"]
    print(df[[c for c in show if c in df.columns]].round(4).to_string(index=False))
    return df, tags


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description="prior 제약 x gamma 정규화 그리드 실험")
    ap.add_argument("--modes", nargs="+", default=list(PRIOR_MODES),
                    choices=list(PRIOR_MODES), help="prior 제약 방식")
    ap.add_argument("--lams", nargs="+", type=float, default=list(LAM_GAMMAS),
                    help="gamma L2 정규화 계수")
    ap.add_argument("--b-bound", type=float, default=DEFAULT_B_BOUND,
                    help="bounded 모드에서 b의 범위. b in [-b_bound, +b_bound]")
    ap.add_argument("--epochs", type=int, default=3000)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", default="experiments.csv", help="outputs/ 아래 저장할 파일명")
    ap.add_argument("--preset", choices=sorted(PRESETS),
                    help="후속실험 조건을 이름으로 지정한다. "
                         "지정하면 --modes/--lams/--b-bound를 덮어쓴다")
    a = ap.parse_args()

    modes, lams, b_bound = tuple(a.modes), tuple(a.lams), a.b_bound
    if a.preset:
        cfg = PRESETS[a.preset]
        modes, lams, b_bound = cfg["modes"], cfg["lams"], cfg["b_bound"]
        print(f"preset={a.preset}: modes={modes} lams={lams} b_bound=±{b_bound}")

    _, run_tags = main(epochs=a.epochs, seed=a.seed, modes=modes,
                       lams=lams, b_bound=b_bound, out_name=a.out)

    # 이번에 돌린 조합만 모은다. 예전 실행분과 섞으면 표가 무너진다.
    suffix = f"_{a.preset}" if a.preset else ""
    collect_params(out_path=OUT_DIR / f"params_comparison{suffix}.csv", tags=run_tags)
