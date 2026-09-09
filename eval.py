"""
Pilot A - eval.py

infer.py가 만든 사후확률 P(LS=1|y), P(LQ=1|y)를
9개 이벤트의 정답(GT)과 비교해 MSE와 AUC를 계산한다.

MSE = 평균( (예측확률 - 정답)^2 )
    정답이 0/1일 때는 Brier score와 같은 값이다.
    낮을수록 좋고, 임계값이 필요 없다.

AUC = ROC 곡선 아래 면적.
    확률의 절대 수준이 아니라 "양성을 음성보다 높게 매겼는가"만 본다.
    후속실험 1의 완료기준이 AUC 기반이라 MSE와 나란히 낸다.
    prior(USGS) 단독 AUC도 같이 내야 사후가 사전보다 나아졌는지 판정할 수 있다.

주의 1: GT는 평가에만 쓴다. train.py로 절대 흘러가면 안 된다.
주의 2: 같은 시정촌코드가 여러 지진 이벤트에 다시 등장하므로
        merge key는 반드시 (event_idx, muni_code)를 함께 써야 한다.
주의 3: LS와 LQ는 평가 가능한 행이 서로 다르다.
        교수님 확정 사항에 따라 각자의 mask로 독립 평가한다.
        joint 상태 평가는 사용하지 않기로 했다.
주의 4: AUC는 양성과 음성이 모두 있어야 정의된다.
        한 클래스만 있는 이벤트는 nan으로 두고 가중평균에서도 제외한다.
        0으로 채우면 "완전히 뒤집힌 예측"과 구분이 안 된다.
"""
import numpy as np
import pandas as pd
from dataclasses import dataclass, field

from sklearn.metrics import roc_auc_score

# 시정촌코드 단독으로 join하면 다른 이벤트의 같은 시정촌과 섞인다.
MERGE_KEYS = ["event_idx", "muni_code"]

# prior 단독 성능을 재려면 pred_df가 USGS prior 확률도 함께 실어와야 한다.
# 없으면 prior 관련 지표만 nan이 되고 나머지는 그대로 나온다.
PRIOR_COLUMNS = {"ls": "prior_ls", "lq": "prior_lq"}


@dataclass
class EvalOutput:
    n: int          # merge된 전체 행 수
    n_ls: int       # ls_eval_mask=True. LS 평가에 실제로 쓰인 행 수
    n_lq: int       # lq_eval_mask=True. LQ 평가에 실제로 쓰인 행 수
    mse_ls: float
    mse_lq: float

    # 평가 가능한 전체 행을 한 덩어리로 본 AUC (이벤트 구분 없음)
    auc_ls: float
    auc_lq: float
    # 같은 행에서 잰 prior(USGS) 단독 AUC. 사후가 이걸 넘어야 한다.
    auc_prior_ls: float
    auc_prior_lq: float

    # 이벤트별로 AUC를 낸 뒤 행 수로 가중평균한 값.
    # pooled AUC는 이벤트 간 확률 수준 차이 때문에 부풀거나 깎일 수 있어 함께 본다.
    auc_ls_wavg: float
    auc_lq_wavg: float
    auc_prior_ls_wavg: float
    auc_prior_lq_wavg: float

    per_event: pd.DataFrame = field(repr=False)
    merged: pd.DataFrame = field(repr=False)


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


def auc(y_true, p):
    """
    y_true: 0/1 정답 배열
    p     : 0~1 예측확률(또는 임의의 점수) 배열

    반환: float. 다음 경우에는 nan이다.
        - 평가 가능한 행이 없음
        - 정답이 전부 0이거나 전부 1 (ROC가 정의되지 않는다)
        - 예측에 NaN이 섞임
    """
    y_true = np.asarray(y_true, dtype=float)
    p = np.asarray(p, dtype=float)
    assert y_true.shape == p.shape, f"shape 불일치: {y_true.shape} vs {p.shape}"

    if y_true.size == 0:
        return float("nan")
    if np.unique(y_true).size < 2:
        return float("nan")
    if not np.isfinite(p).all():
        return float("nan")

    return float(roc_auc_score(y_true, p))


def _mask(df, column):
    """mask 컬럼이 있으면 bool로, 없으면 전부 True로 돌려준다."""
    if column in df.columns:
        return df[column].astype(bool)
    return pd.Series(True, index=df.index)


def _auc_of(rows, true_col, score_col):
    """score_col이 없으면(예: prior를 안 넘긴 경우) nan을 돌려준다."""
    if score_col not in rows.columns:
        return float("nan")
    return auc(rows[true_col], rows[score_col])


def _weighted_mean(values, weights):
    """AUC가 정의된 이벤트만 골라 행 수로 가중평균한다."""
    values = np.asarray(values, dtype=float)
    weights = np.asarray(weights, dtype=float)

    ok = np.isfinite(values) & (weights > 0)
    if not ok.any():
        return float("nan")
    return float(np.sum(values[ok] * weights[ok]) / np.sum(weights[ok]))


def _per_event_table(merged, ls_mask, lq_mask):
    """이벤트별 MSE/AUC 표를 만든다. 완료기준이 '2004 니가타 LS AUC'라 분해가 필수다."""
    rows = []
    for event_idx in sorted(merged["event_idx"].unique()):
        in_event = merged["event_idx"] == event_idx
        ls_rows = merged.loc[in_event & ls_mask]
        lq_rows = merged.loc[in_event & lq_mask]

        row = {"event_idx": int(event_idx)}
        # 이벤트명 컬럼은 gt_df에 있으면 따라온다. 없으면 생략한다.
        if "event" in merged.columns:
            names = merged.loc[in_event, "event"].unique()
            row["event"] = names[0] if len(names) else ""

        row.update({
            "n_ls": len(ls_rows),
            "n_pos_ls": int(ls_rows["ls_true"].sum()) if len(ls_rows) else 0,
            "mse_ls": mse(ls_rows["ls_true"], ls_rows["p_ls"]),
            "auc_ls": auc(ls_rows["ls_true"], ls_rows["p_ls"]),
            "auc_prior_ls": _auc_of(ls_rows, "ls_true", PRIOR_COLUMNS["ls"]),

            "n_lq": len(lq_rows),
            "n_pos_lq": int(lq_rows["lq_true"].sum()) if len(lq_rows) else 0,
            "mse_lq": mse(lq_rows["lq_true"], lq_rows["p_lq"]),
            "auc_lq": auc(lq_rows["lq_true"], lq_rows["p_lq"]),
            "auc_prior_lq": _auc_of(lq_rows, "lq_true", PRIOR_COLUMNS["lq"]),
        })
        rows.append(row)

    return pd.DataFrame(rows)


def evaluate(gt_df, pred_df):
    """
    pred_df : event_idx / muni_code / p_ls / p_lq
              + prior_ls / prior_lq (있으면 prior 단독 AUC도 함께 계산한다)
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

    per_event = _per_event_table(merged, ls_mask, lq_mask)

    return EvalOutput(
        n=len(merged),
        n_ls=len(ls_rows),
        n_lq=len(lq_rows),
        mse_ls=mse(ls_rows["ls_true"], ls_rows["p_ls"]),
        mse_lq=mse(lq_rows["lq_true"], lq_rows["p_lq"]),

        auc_ls=auc(ls_rows["ls_true"], ls_rows["p_ls"]),
        auc_lq=auc(lq_rows["lq_true"], lq_rows["p_lq"]),
        auc_prior_ls=_auc_of(ls_rows, "ls_true", PRIOR_COLUMNS["ls"]),
        auc_prior_lq=_auc_of(lq_rows, "lq_true", PRIOR_COLUMNS["lq"]),

        auc_ls_wavg=_weighted_mean(per_event["auc_ls"], per_event["n_ls"]),
        auc_lq_wavg=_weighted_mean(per_event["auc_lq"], per_event["n_lq"]),
        auc_prior_ls_wavg=_weighted_mean(per_event["auc_prior_ls"], per_event["n_ls"]),
        auc_prior_lq_wavg=_weighted_mean(per_event["auc_prior_lq"], per_event["n_lq"]),

        per_event=per_event,
        merged=merged,
    )
