"""
Pilot A - eval.py

infer.py가 만든 사후확률 P(LS=1|y), P(LQ=1|y)를
9개 이벤트의 정답(GT)과 비교해 MSE를 계산한다.

MSE = 평균( (예측확률 - 정답)^2 )
    정답이 0/1일 때는 Brier score와 같은 값이다.
    낮을수록 좋고, 임계값이 필요 없다.

주의 1: GT는 평가에만 쓴다. train.py로 절대 흘러가면 안 된다.
주의 2: 같은 시정촌코드가 여러 지진 이벤트에 다시 등장하므로
        merge key는 반드시 (event_idx, muni_code)를 함께 써야 한다.
주의 3: LS와 LQ는 평가 가능한 행이 서로 다르다.
        교수님 확정 사항에 따라 각자의 mask로 독립 평가한다.
        joint 상태 평가는 사용하지 않기로 했다.
"""
import numpy as np
import pandas as pd
from dataclasses import dataclass

# 시정촌코드 단독으로 join하면 다른 이벤트의 같은 시정촌과 섞인다.
MERGE_KEYS = ["event_idx", "muni_code"]


@dataclass
class EvalOutput:
    n: int          # merge된 전체 행 수
    n_ls: int       # ls_eval_mask=True. LS MSE에 실제로 쓰인 행 수
    n_lq: int       # lq_eval_mask=True. LQ MSE에 실제로 쓰인 행 수
    mse_ls: float
    mse_lq: float
    merged: pd.DataFrame


def mse(y_true, p):
    """
    y_true: 0/1 정답 배열
    p     : 0~1 예측확률 배열

    반환: float. 평가 가능한 행이 없으면 nan
    """
    y_true = np.asarray(y_true, dtype=float)
    p = np.asarray(p, dtype=float)
    assert y_true.shape == p.shape, f"shape 불일치: {y_true.shape} vs {p.shape}"
    if y_true.size == 0:
        return float("nan")
    return float(np.mean((y_true - p) ** 2))


def _mask(df, column):
    """mask 컬럼이 있으면 bool로, 없으면 전부 True로 돌려준다."""
    if column in df.columns:
        return df[column].astype(bool)
    return pd.Series(True, index=df.index)


def evaluate(gt_df, pred_df):
    """
    pred_df : event_idx / muni_code / p_ls / p_lq
    gt_df   : event_idx / muni_code / ls_true / lq_true
              + ls_eval_mask / lq_eval_mask (없으면 전 행을 평가 대상으로 본다)

    반환: EvalOutput
    """
    for name, df in (("gt_df", gt_df), ("pred_df", pred_df)):
        missing_cols = [c for c in MERGE_KEYS if c not in df.columns]
        if missing_cols:
            raise ValueError(f"{name}에 merge key가 없습니다: {missing_cols}")

    gt_keys = set(map(tuple, gt_df[MERGE_KEYS].to_numpy().tolist()))
    pred_keys = set(map(tuple, pred_df[MERGE_KEYS].to_numpy().tolist()))
    missing = gt_keys - pred_keys
    if missing:
        print(f"[경고] 예측에 없는 GT (event_idx, muni_code) {len(missing)}개: {sorted(missing)[:10]}")

    merged = pd.merge(gt_df, pred_df, on=MERGE_KEYS, how="left", validate="one_to_one")

    # how="left"라 예측이 없는 GT 행은 NaN이 된다. 그대로 두면 MSE가 NaN이 되므로 여기서 잡는다.
    no_pred = merged["p_ls"].isna() | merged["p_lq"].isna()
    if no_pred.any():
        raise ValueError(
            "예측값이 없는 GT 행이 있습니다: "
            f"{merged.loc[no_pred, MERGE_KEYS].to_dict('records')[:10]}"
        )

    # 원본이 NA인 행의 정답은 Tensor 저장용 placeholder 0이라 평가에 쓰면 안 된다.
    # LS와 LQ는 규칙이 달라 평가 가능한 행도 서로 다르므로 각자의 mask로 자른다.
    ls_mask = _mask(merged, "ls_eval_mask")
    lq_mask = _mask(merged, "lq_eval_mask")

    ls_rows = merged.loc[ls_mask]
    lq_rows = merged.loc[lq_mask]

    return EvalOutput(
        n=len(merged),
        n_ls=len(ls_rows),
        n_lq=len(lq_rows),
        mse_ls=mse(ls_rows["ls_true"], ls_rows["p_ls"]),
        mse_lq=mse(lq_rows["lq_true"], lq_rows["p_lq"]),
        merged=merged,
    )
