"""
Pilot A - eval.py

infer.py가 만든 사후확률 P(LS=1|y), P(LQ=1|y)를
이부리 지진의 정답(GT)과 비교해 MSE를 계산한다.

MSE = 평균( (예측확률 - 정답)^2 )
    정답이 0/1일 때는 Brier score와 같은 값이다.
    낮을수록 좋고, 임계값이 필요 없다.

주의: GT는 평가에만 쓴다. train.py로 절대 흘러가면 안 된다.
"""
import numpy as np
import pandas as pd
from dataclasses import dataclass

@dataclass
class EvalOutput:
    n: int          # 평가에 쓴 전체 행 수 (LQ 기준)
    n_ls: int       # LS GT가 실제 존재하는 행 수 (ls_eval_mask=True)
    mse_ls: float
    mse_lq: float
    merged: pd.DataFrame


def mse(y_true, p):
    """
    y_true: 0/1 정답 배열
    p     : 0~1 예측확률 배열

    반환: float
    """
    y_true = np.asarray(y_true, dtype=float)
    p = np.asarray(p, dtype=float)
    assert y_true.shape == p.shape, f"shape 불일치: {y_true.shape} vs {p.shape}"
    if y_true.size == 0:
        return float("nan")
    return float(np.mean((y_true - p) ** 2))


def evaluate(gt_df, pred_df):
    """
    pred_df : muni_code / p_ls / p_lq        (이부리 예측 행)
    gt_df   : muni_code / ls_true / lq_true / ls_eval_mask(선택)

    반환: EvalOutput
    """
    missing = set(gt_df["muni_code"]) - set(pred_df["muni_code"])
    if missing:
        print(f"[경고] 예측에 없는 GT 시정촌 {len(missing)}개: {sorted(missing)}")

    merged = pd.merge(gt_df, pred_df, on="muni_code", how="left", validate="one_to_one")

    # how="left"라 예측이 없는 GT 행은 NaN이 된다. 그대로 두면 MSE가 NaN이 되므로 여기서 잡는다.
    no_pred = merged["p_ls"].isna() | merged["p_lq"].isna()
    if no_pred.any():
        raise ValueError(
            "예측값이 없는 GT 시정촌이 있습니다: "
            f"{merged.loc[no_pred, 'muni_code'].tolist()}"
        )

    # LS 원본이 NA인 행은 schema/loader 규칙대로 LS 평가에서 제외한다.
    if "ls_eval_mask" in merged.columns:
        ls_rows = merged.loc[merged["ls_eval_mask"].astype(bool)]
    else:
        ls_rows = merged

    return EvalOutput(
        n=len(merged),
        n_ls=len(ls_rows),
        mse_ls=mse(ls_rows["ls_true"], ls_rows["p_ls"]),
        mse_lq=mse(merged["lq_true"], merged["p_lq"]),
        merged=merged,
    )
