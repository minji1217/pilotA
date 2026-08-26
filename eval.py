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
    n: int
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
    return float(np.mean((y_true - p) ** 2))


def evaluate( gt_df,pred_df):
    """
    pred_df : muni_code / p_ls / p_lq   (이부리 42행)
    gt_df   : muni_code / ls_true / lq_true

    반환: dict
    """
    # 3) muni_code로 붙이기
    #    how는 뭘 쓸까? validate 옵션도 생각해볼 것
    missing = set(gt_df["muni_code"]) - set(pred_df["muni_code"])
    if missing:
        print(f"[경고] 예측에 없는 GT 시정촌 {len(missing)}개: {sorted(missing)}")

    merged = pd.merge(gt_df,pred_df,on="muni_code",how="left",validate="one_to_one")

    return EvalOutput(
        n=len(merged),
        mse_ls=mse(merged["ls_true"], merged["p_ls"]),
        mse_lq=mse(merged["lq_true"], merged["p_lq"]),
        merged=merged
    )

