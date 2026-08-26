"""
Pilot A - data/loader.py

이 모듈은 실제 피해 통계 XLSX와 USGS XLSX를 읽어 PilotABatch를 만든다.

처리 순서:
1. 이벤트 시트의 실제 헤더를 찾는다.
2. 합계/소계가 아닌 실제 시정촌 행만 남긴다.
3. 시정촌코드를 5자리 문자열로 정규화한다. 예: 1581 -> "01581"
4. 피해 6채널의 결측을 y=0 placeholder + obs_mask=False로 분리한다.
5. 같은 이벤트 안에서 5자리 시정촌코드로 통계와 USGS를 join한다.
6. LS_prior(평균), LQ_prior(평균), PGV와 Exposure가 모두 있는 행만 남긴다.
7. population / households_general로 E를 만든다.
8. PyTorch PilotABatch로 변환하고 batch.validate()를 실행한다.
9. eval용 GT가 필요하면 LS_LF 데이터자료.xlsx를 읽어 EvalGroundTruthBatch를 별도로 만든다.

중요: 시정촌코드는 계산용 숫자가 아니라 ID이므로 int로 바꾸어 보관하지 않는다.
GT는 모델 입력이 아니므로 PilotABatch에 넣지 않고 EvalGroundTruthBatch로 분리한다.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

import pandas as pd
import torch

from .schema import (
    CHANNELS,
    DAMAGE_COLUMN_MAP,
    DTYPE,
    EVENTS,
    EVENT_TO_INDEX,
    EXPECTED_NUM_MODEL_ROWS,
    EXPECTED_NUM_STATS_ROWS,
    EXPECTED_NUM_USGS_MATCHED_ROWS,
    EXPOSURE_COLUMN_BY_CHANNEL,
    HOUSEHOLDS_COLUMN,
    INDEX_DTYPE,
    MUNICIPALITY_CODE_COLUMN,
    MUNICIPALITY_CODE_WIDTH,
    POPULATION_COLUMN,
    USGS_LQ_PRIOR_COLUMN,
    USGS_LS_PRIOR_COLUMN,
    USGS_PGV_COLUMN,
    EvalGroundTruthBatch,
    PilotABatch,
)


# 통계 XLSX에서 모델 입력을 만들기 위해 반드시 필요한 컬럼이다.
STATS_REQUIRED_COLUMNS: tuple[str, ...] = (
    MUNICIPALITY_CODE_COLUMN,
    *tuple(DAMAGE_COLUMN_MAP[channel] for channel in CHANNELS),
    POPULATION_COLUMN,
    HOUSEHOLDS_COLUMN,
)

# USGS XLSX에서는 평균 prior 두 개와 PGV만 사용한다.
USGS_REQUIRED_COLUMNS: tuple[str, ...] = (
    MUNICIPALITY_CODE_COLUMN,
    USGS_LS_PRIOR_COLUMN,
    USGS_LQ_PRIOR_COLUMN,
    USGS_PGV_COLUMN,
)


# 현재 실제 GT 파일은 2018 훗카이도 한 이벤트의 LS/LQ 정답을 제공한다.
EVAL_EVENT_NAME: str = "2018 훗카이도"
EVAL_LS_SHEET_NAME: str = "2018 훗카이도(LS)"
EVAL_LQ_SHEET_NAME: str = "2018 훗카이도 (LF)"
GT_CODE_COLUMN: str = "muni_code"
GT_LS_AREA_COLUMN: str = "ls_area_ha"
GT_LQ_FLAG_COLUMN: str = "jshis_flag"

# LF GT는 삿포로시가 01101~01110의 10개 구로 나뉘어 있지만 모델 데이터는 삿포로시 01100 한 행이다.
# 평가 시에는 어느 한 구라도 LQ GT=1이면 삿포로시 전체 GT를 1로 보는 max 집계를 사용한다.
SAPPORO_CITY_CODE: str = "01100"
SAPPORO_WARD_CODES: frozenset[str] = frozenset(
    f"011{ward:02d}" for ward in range(1, 11)
)


def _normalize_municipality_code(value: object) -> str | None:
    """
    Excel에서 읽은 시정촌코드를 앞자리 0을 포함한 5자리 문자열로 변환한다.

    입력 예: 1581, 1581.0, "1581", "01581"
    출력 예: 모두 "01581"
    빈 값이나 숫자로 해석할 수 없는 값은 None을 반환한다.

    이유: 시정촌코드는 수치 계산 대상이 아니라 ID이므로 01581과 같은 앞자리 0을 보존해야 한다.
    """
    if pd.isna(value):
        return None

    text = str(value).strip()
    if not text:
        return None

    # Excel 숫자 셀은 pandas에서 1581.0처럼 읽힐 수 있으므로 먼저 숫자로 해석한다.
    numeric = pd.to_numeric(text, errors="coerce")
    if pd.isna(numeric):
        return None

    # 시정촌코드는 정수형 ID이므로 1581.5 같은 값은 정상 코드로 인정하지 않는다.
    numeric_float = float(numeric)
    if not numeric_float.is_integer():
        return None

    # int 변환은 정규화 과정에서만 사용하고 최종 저장은 다시 5자리 문자열로 한다.
    code = str(int(numeric_float)).zfill(MUNICIPALITY_CODE_WIDTH)
    if len(code) != MUNICIPALITY_CODE_WIDTH:
        raise ValueError(
            f"시정촌코드는 {MUNICIPALITY_CODE_WIDTH}자리여야 합니다: raw={value!r}, normalized={code!r}"
        )

    return code


def _find_header_row(path: str | Path, sheet_name: str) -> int:
    """
    Excel 시트에서 실제 표의 헤더 행 번호를 찾는다.

    입력: XLSX 경로, 이벤트 시트명
    출력: 실제 헤더의 0-based 행 번호
    이유: 현재 파일은 제목·설명·빈 줄 뒤에 실제 표가 시작하므로 header=0을 고정하면 안 된다.
    """
    # header=None으로 모든 행을 데이터로 읽어 실제 헤더 후보를 직접 찾는다.
    raw = pd.read_excel(path, sheet_name=sheet_name, header=None)

    for row_idx, row in raw.iterrows():
        # NaN은 제외하고 셀 값을 문자열 집합으로 바꿔 컬럼명 존재 여부를 확인한다.
        values = {str(value).strip() for value in row.tolist() if pd.notna(value)}

        # 통계와 USGS의 실제 헤더에는 공통으로 '부현'과 '시정촌코드'가 존재한다.
        if "부현" in values and MUNICIPALITY_CODE_COLUMN in values:
            return int(row_idx)

    raise ValueError(
        f"[{sheet_name}] 실제 헤더 행을 찾지 못했습니다. "
        f"'{MUNICIPALITY_CODE_COLUMN}' 컬럼이 있는지 확인하세요."
    )


def _read_table(path: str | Path, sheet_name: str) -> pd.DataFrame:
    """
    제목·설명 행을 건너뛰고 실제 표만 DataFrame으로 읽는다.

    입력: XLSX 경로, 이벤트 시트명
    출력: 실제 컬럼명을 가진 pandas.DataFrame
    """
    header_row = _find_header_row(path, sheet_name)

    # 찾은 실제 헤더 행을 pandas의 header로 지정한다.
    df = pd.read_excel(path, sheet_name=sheet_name, header=header_row)

    # 완전히 빈 컬럼은 전처리에 필요하지 않으므로 제거한다.
    df = df.dropna(axis=1, how="all")

    return df.copy()


def _require_columns(
    df: pd.DataFrame,
    required_columns: Iterable[str],
    *,
    sheet_name: str,
    source_name: str,
) -> None:
    """
    필요한 컬럼이 실제 시트에 모두 있는지 검사한다.

    입력: DataFrame, 필수 컬럼 목록, 시트명, 자료 종류
    출력: 정상 None, 누락 컬럼이 있으면 ValueError
    """
    missing = [column for column in required_columns if column not in df.columns]
    if missing:
        raise ValueError(f"[{sheet_name}] {source_name} 필수 컬럼이 없습니다: {missing}")


def _keep_municipality_rows(
    df: pd.DataFrame,
    *,
    sheet_name: str,
    source_name: str,
) -> pd.DataFrame:
    """
    합계·소계·설명 행을 제거하고 실제 시정촌 행만 남긴다.

    입력: 원본 표 DataFrame
    출력: 시정촌코드가 "01581" 같은 5자리 문자열로 정규화된 DataFrame

    합계 행처럼 시정촌코드가 비어 있거나 코드로 해석할 수 없는 행은 제거한다.
    """
    result = df.copy()

    # 각 셀을 5자리 문자열 코드로 정규화한다. 예: 1581.0 -> "01581"
    normalized_codes = result[MUNICIPALITY_CODE_COLUMN].map(_normalize_municipality_code)

    # 정상 코드가 만들어진 행만 실제 시정촌 행으로 남긴다.
    valid_code_mask = normalized_codes.notna()
    result = result.loc[valid_code_mask].copy()

    # int가 아니라 문자열 자체를 저장해 leading zero를 보존한다.
    result[MUNICIPALITY_CODE_COLUMN] = normalized_codes.loc[valid_code_mask].astype(str)

    # 한 이벤트 안에서 동일 시정촌코드가 중복되면 one-to-one join을 보장할 수 없으므로 즉시 중단한다.
    if result[MUNICIPALITY_CODE_COLUMN].duplicated().any():
        duplicates = result.loc[
            result[MUNICIPALITY_CODE_COLUMN].duplicated(keep=False),
            MUNICIPALITY_CODE_COLUMN,
        ].tolist()
        raise ValueError(f"[{sheet_name}] {source_name}에 중복 시정촌코드가 있습니다: {duplicates}")

    return result.reset_index(drop=True)


def _parse_damage_column(
    series: pd.Series,
    *,
    sheet_name: str,
    column_name: str,
) -> tuple[pd.Series, pd.Series]:
    """
    피해 한 채널을 숫자 y와 관측 여부 mask로 분리한다.

    입력 예: [1097, "-", 0]
    출력 예: values=[1097.0,0.0,0.0], observed=[True,False,True]

    '-'는 실제 0건이 아니라 결측이다. y에는 계산용 placeholder 0을 넣고 obs_mask=False로 보존한다.
    """
    # 문자열 앞뒤 공백을 없애 " - " 같은 값도 정상 결측으로 인식한다.
    stripped = series.astype("string").str.strip()

    # 빈 셀과 여러 종류의 dash 문자를 결측으로 본다.
    missing = series.isna() | stripped.isin(["", "-", "–", "—"])

    # 결측이 아닌 값만 숫자로 변환한다. 이상 문자열은 NaN이 되어 아래 invalid 검사에서 잡힌다.
    numeric = pd.to_numeric(series.where(~missing), errors="coerce")

    invalid = (~missing) & numeric.isna()
    if invalid.any():
        bad_values = series.loc[invalid].astype(str).unique().tolist()
        raise ValueError(
            f"[{sheet_name}] '{column_name}'에 숫자도 결측표시도 아닌 값이 있습니다: {bad_values}"
        )

    # PyTorch count Tensor는 숫자여야 하므로 결측 위치에는 0 placeholder를 넣는다.
    values = numeric.fillna(0.0).astype("float64")

    # 실제 관측값이면 True, 결측이면 False다.
    observed = (~missing).astype(bool)

    return values, observed


def _prepare_stats_sheet(path: str | Path, sheet_name: str) -> pd.DataFrame:
    """
    한 이벤트의 피해 통계 시트를 join 직전 형태로 정리한다.

    출력: 시정촌코드, 피해 6채널, obs_* 6개, population, households_general
    """
    df = _read_table(path, sheet_name)
    _require_columns(df, STATS_REQUIRED_COLUMNS, sheet_name=sheet_name, source_name="통계")
    df = _keep_municipality_rows(df, sheet_name=sheet_name, source_name="통계")

    result = pd.DataFrame()

    # 이미 _keep_municipality_rows()에서 5자리 문자열로 정규화된 코드를 그대로 복사한다.
    result[MUNICIPALITY_CODE_COLUMN] = df[MUNICIPALITY_CODE_COLUMN].astype(str)

    # schema.py의 CHANNELS 순서대로 피해값과 mask를 생성한다.
    for channel in CHANNELS:
        source_column = DAMAGE_COLUMN_MAP[channel]
        values, observed = _parse_damage_column(
            df[source_column],
            sheet_name=sheet_name,
            column_name=source_column,
        )
        result[channel] = values
        result[f"obs_{channel}"] = observed

    # Exposure 원본값은 여기서 숫자로만 변환하고 실제 사용 가능 여부는 join 이후에 판단한다.
    result[POPULATION_COLUMN] = pd.to_numeric(
        df[POPULATION_COLUMN],
        errors="coerce",
    ).astype("float64")
    result[HOUSEHOLDS_COLUMN] = pd.to_numeric(
        df[HOUSEHOLDS_COLUMN],
        errors="coerce",
    ).astype("float64")

    return result


def _prepare_usgs_sheet(path: str | Path, sheet_name: str) -> pd.DataFrame:
    """
    한 이벤트의 USGS 시트를 이번 Pilot에 필요한 값만 남겨 정리한다.

    출력: 시정촌코드, pi_ls=LS_prior(평균), pi_lq=LQ_prior(평균), pgv=PGV
    """
    df = _read_table(path, sheet_name)
    _require_columns(df, USGS_REQUIRED_COLUMNS, sheet_name=sheet_name, source_name="USGS")
    df = _keep_municipality_rows(df, sheet_name=sheet_name, source_name="USGS")

    result = pd.DataFrame()
    result[MUNICIPALITY_CODE_COLUMN] = df[MUNICIPALITY_CODE_COLUMN].astype(str)

    # 이번 Pilot에서 확정한 평균 prior를 모델 변수명으로 바꿔 저장한다.
    result["pi_ls"] = pd.to_numeric(df[USGS_LS_PRIOR_COLUMN], errors="coerce")
    result["pi_lq"] = pd.to_numeric(df[USGS_LQ_PRIOR_COLUMN], errors="coerce")
    result["pgv"] = pd.to_numeric(df[USGS_PGV_COLUMN], errors="coerce")

    # 실제 값이 존재하는 prior가 [0,1] 범위를 벗어나면 데이터 오류로 처리한다.
    for prior_name in ("pi_ls", "pi_lq"):
        valid = result[prior_name].notna()
        out_of_range = valid & ((result[prior_name] < 0) | (result[prior_name] > 1))
        if out_of_range.any():
            bad_codes = result.loc[out_of_range, MUNICIPALITY_CODE_COLUMN].tolist()
            raise ValueError(f"[{sheet_name}] {prior_name}가 [0,1] 범위를 벗어났습니다: {bad_codes}")

    return result


def _merge_event(
    stats_df: pd.DataFrame,
    usgs_df: pd.DataFrame,
    sheet_name: str,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    같은 이벤트의 통계와 USGS를 5자리 시정촌코드로 join한다.

    출력:
    - model_df: 현재 모델에 필요한 값이 모두 있는 행
    - excluded_df: USGS/PGV/prior/Exposure 문제로 제외된 행

    이벤트 시트별로 따로 처리하므로 실질적인 key는 이벤트 + 시정촌코드다.
    """
    # 통계를 기준으로 left join해 USGS에 없는 시정촌도 제외 사유를 확인할 수 있게 한다.
    merged = stats_df.merge(
        usgs_df,
        on=MUNICIPALITY_CODE_COLUMN,
        how="left",
        validate="one_to_one",
        indicator=True,
    )

    has_usgs_row = merged["_merge"].eq("both")
    has_usgs_values = merged[["pgv", "pi_ls", "pi_lq"]].notna().all(axis=1)
    has_exposure = merged[[POPULATION_COLUMN, HOUSEHOLDS_COLUMN]].notna().all(axis=1)
    positive_exposure = (
        (merged[POPULATION_COLUMN] > 0)
        & (merged[HOUSEHOLDS_COLUMN] > 0)
    )
    positive_pgv = merged["pgv"] > 0

    # 현재 회귀식과 prior 계산에 필요한 조건을 모두 만족해야 모델 행으로 사용한다.
    usable = (
        has_usgs_row
        & has_usgs_values
        & has_exposure
        & positive_exposure
        & positive_pgv
    )

    model_df = merged.loc[usable].drop(columns="_merge").copy()

    # 제외 행은 버리지 않고 원인 분석용으로 별도 보관한다.
    excluded_df = merged.loc[~usable].copy()
    excluded_df["exclude_reason"] = ""
    excluded_df.loc[~has_usgs_row, "exclude_reason"] += "USGS 행 없음; "
    excluded_df.loc[has_usgs_row & ~has_usgs_values, "exclude_reason"] += "PGV/prior 결측; "
    excluded_df.loc[~has_exposure, "exclude_reason"] += "Exposure 결측; "
    excluded_df.loc[has_exposure & ~positive_exposure, "exclude_reason"] += "Exposure 0 이하; "
    excluded_df.loc[has_usgs_values & ~positive_pgv, "exclude_reason"] += "PGV 0 이하; "

    # regression.py에서 이벤트별 alpha_e를 선택할 수 있도록 0~7 index를 저장한다.
    model_df["event_idx"] = EVENT_TO_INDEX[sheet_name]

    # 제외 데이터에는 사람이 읽을 수 있도록 이벤트명도 보존한다.
    excluded_df["event"] = sheet_name

    return model_df.reset_index(drop=True), excluded_df.reset_index(drop=True)


def _add_exposure_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    population / households_general을 6채널 Exposure E로 확장한다.

    예: population=4838, households_general=2121
    -> E=[4838,4838,4838,2121,2121,2121]
    """
    result = df.copy()

    for channel in CHANNELS:
        source_column = EXPOSURE_COLUMN_BY_CHANNEL[channel]
        result[f"E_{channel}"] = result[source_column].astype("float64")

    return result


def _to_batch(df: pd.DataFrame) -> PilotABatch:
    """
    정리된 DataFrame을 A/B 공통 PilotABatch로 변환한다.

    시정촌코드는 Tensor로 바꾸지 않고 5자리 문자열 tuple로 그대로 보존한다.
    """
    y_columns = list(CHANNELS)
    e_columns = [f"E_{channel}" for channel in CHANNELS]
    mask_columns = [f"obs_{channel}" for channel in CHANNELS]

    batch = PilotABatch(
        y=torch.tensor(
            df[y_columns].to_numpy(dtype="float64"),
            dtype=DTYPE,
        ),
        E=torch.tensor(
            df[e_columns].to_numpy(dtype="float64"),
            dtype=DTYPE,
        ),
        pgv=torch.tensor(
            df["pgv"].to_numpy(dtype="float64"),
            dtype=DTYPE,
        ),
        pi_ls=torch.tensor(
            df["pi_ls"].to_numpy(dtype="float64"),
            dtype=DTYPE,
        ),
        pi_lq=torch.tensor(
            df["pi_lq"].to_numpy(dtype="float64"),
            dtype=DTYPE,
        ),
        event_idx=torch.tensor(
            df["event_idx"].to_numpy(dtype="int64"),
            dtype=INDEX_DTYPE,
        ),
        obs_mask=torch.tensor(
            df[mask_columns].to_numpy(dtype=bool),
            dtype=torch.bool,
        ),

        # ID는 계산 대상이 아니므로 "01581" 같은 문자열 자체를 tuple로 저장한다.
        municipality_code=tuple(
            df[MUNICIPALITY_CODE_COLUMN].astype(str).tolist()
        ),
    )

    batch.validate()
    return batch


def _load_all_events(
    stats_path: str | Path,
    usgs_path: str | Path,
) -> tuple[pd.DataFrame, pd.DataFrame, int, int]:
    """
    8개 이벤트 전체에 같은 전처리 규칙을 적용한다.

    출력: 전체 model_df, 전체 excluded_df, 통계 원본 행 수, USGS 매칭 행 수
    """
    model_frames: list[pd.DataFrame] = []
    excluded_frames: list[pd.DataFrame] = []
    total_stats_rows = 0
    total_usgs_matched_rows = 0

    for event in EVENTS:
        stats_df = _prepare_stats_sheet(stats_path, event)
        usgs_df = _prepare_usgs_sheet(usgs_path, event)

        total_stats_rows += len(stats_df)

        model_df, excluded_df = _merge_event(stats_df, usgs_df, event)

        # model_df는 모두 USGS 매칭 행이고, excluded_df 중 _merge=="both"인 행도 USGS 자체는 존재한다.
        event_usgs_matched_rows = len(model_df) + int(
            excluded_df["_merge"].eq("both").sum()
        )
        total_usgs_matched_rows += event_usgs_matched_rows

        model_frames.append(model_df)
        excluded_frames.append(excluded_df)

    all_model_df = pd.concat(model_frames, ignore_index=True)
    all_excluded_df = pd.concat(excluded_frames, ignore_index=True)

    return (
        all_model_df,
        all_excluded_df,
        total_stats_rows,
        total_usgs_matched_rows,
    )


def load_pilot_a_batch(
    stats_path: str | Path,
    usgs_path: str | Path,
    *,
    strict_expected_rows: bool = True,
) -> PilotABatch:
    """
    실제 통계 XLSX와 USGS XLSX를 읽어 최종 PilotABatch를 만든다.

    입력:
    - stats_path: 재난프로젝트_시정촌별_통계데이터.xlsx
    - usgs_path: 재난프로젝트_시정촌별_USGS.xlsx
    - strict_expected_rows: True이면 현재 확인한 403/383/382 행 수가 맞는지 검사

    출력: PilotABatch
    """
    stats_path = Path(stats_path)
    usgs_path = Path(usgs_path)

    if not stats_path.exists():
        raise FileNotFoundError(f"통계 XLSX를 찾을 수 없습니다: {stats_path}")
    if not usgs_path.exists():
        raise FileNotFoundError(f"USGS XLSX를 찾을 수 없습니다: {usgs_path}")

    model_df, _, total_stats_rows, total_usgs_matched_rows = _load_all_events(
        stats_path,
        usgs_path,
    )

    model_df = _add_exposure_columns(model_df)

    # 현재 실제 파일이 우리가 확인한 상태와 동일한지 점검한다.
    if strict_expected_rows:
        if total_stats_rows != EXPECTED_NUM_STATS_ROWS:
            raise ValueError(
                f"통계 원본 행 수가 예상과 다릅니다: "
                f"expected={EXPECTED_NUM_STATS_ROWS}, actual={total_stats_rows}"
            )
        if total_usgs_matched_rows != EXPECTED_NUM_USGS_MATCHED_ROWS:
            raise ValueError(
                f"USGS 매칭 행 수가 예상과 다릅니다: "
                f"expected={EXPECTED_NUM_USGS_MATCHED_ROWS}, actual={total_usgs_matched_rows}"
            )
        if len(model_df) != EXPECTED_NUM_MODEL_ROWS:
            raise ValueError(
                f"최종 모델 행 수가 예상과 다릅니다: "
                f"expected={EXPECTED_NUM_MODEL_ROWS}, actual={len(model_df)}"
            )

    return _to_batch(model_df)


def load_excluded_rows(
    stats_path: str | Path,
    usgs_path: str | Path,
) -> pd.DataFrame:
    """
    현재 모델에서 제외되는 시정촌과 제외 사유를 반환한다.

    학습 함수가 아니라 데이터 점검용 함수다.
    """
    _, excluded_df, _, _ = _load_all_events(stats_path, usgs_path)
    return excluded_df


def _prepare_ls_ground_truth(gt_path: str | Path) -> pd.DataFrame:
    """
    LS GT 시트를 시정촌코드 + gt_ls(0/1) 형태로 정리한다.

    현재 원본 규칙:
    - ls_area_ha > 0  -> gt_ls=1
    - ls_area_ha == 0 -> gt_ls=0
    - NaN / "NA"  -> gt_ls=0

    사용자가 확정한 eval 규칙에 따라 GT의 결측은 '발생 없음(0)'으로 처리한다.
    """
    df = pd.read_excel(gt_path, sheet_name=EVAL_LS_SHEET_NAME)
    required = [GT_CODE_COLUMN, GT_LS_AREA_COLUMN]
    missing = [column for column in required if column not in df.columns]
    if missing:
        raise ValueError(
            f"[{EVAL_LS_SHEET_NAME}] GT 필수 컬럼이 없습니다: {missing}"
        )

    result = pd.DataFrame()
    result[MUNICIPALITY_CODE_COLUMN] = df[GT_CODE_COLUMN].map(
        _normalize_municipality_code
    )
    result = result.loc[result[MUNICIPALITY_CODE_COLUMN].notna()].copy()

    # pd.to_numeric(..., errors='coerce')로 문자열 'NA'도 NaN으로 만든 뒤 0으로 처리한다.
    ls_area = pd.to_numeric(df.loc[result.index, GT_LS_AREA_COLUMN], errors="coerce")
    ls_area = ls_area.fillna(0.0).astype("float64")

    if (ls_area < 0).any():
        bad_codes = result.loc[ls_area < 0, MUNICIPALITY_CODE_COLUMN].tolist()
        raise ValueError(
            f"[{EVAL_LS_SHEET_NAME}] ls_area_ha는 음수가 될 수 없습니다: {bad_codes}"
        )

    result["gt_ls"] = (ls_area > 0).astype("int64")

    if result[MUNICIPALITY_CODE_COLUMN].duplicated().any():
        duplicates = result.loc[
            result[MUNICIPALITY_CODE_COLUMN].duplicated(keep=False),
            MUNICIPALITY_CODE_COLUMN,
        ].tolist()
        raise ValueError(
            f"[{EVAL_LS_SHEET_NAME}] 중복 시정촌코드가 있습니다: {duplicates}"
        )

    return result[[MUNICIPALITY_CODE_COLUMN, "gt_ls"]].reset_index(drop=True)


def _prepare_lq_ground_truth(gt_path: str | Path) -> pd.DataFrame:
    """
    LF(LQ) GT 시트를 시정촌코드 + gt_lq(0/1) 형태로 정리한다.

    현재 원본 규칙:
    - jshis_flag == 1 -> gt_lq=1
    - jshis_flag == 0 -> gt_lq=0
    - NaN / "NA"   -> gt_lq=0

    LF 원본만 삿포로시가 01101~01110의 10개 구로 분리되어 있으므로
    모델의 삿포로시 코드 01100으로 합치고 max(gt_lq)를 사용한다.
    즉 10개 구 중 하나라도 1이면 삿포로시 gt_lq=1이다.
    """
    df = pd.read_excel(gt_path, sheet_name=EVAL_LQ_SHEET_NAME)
    required = [GT_CODE_COLUMN, GT_LQ_FLAG_COLUMN]
    missing = [column for column in required if column not in df.columns]
    if missing:
        raise ValueError(
            f"[{EVAL_LQ_SHEET_NAME}] GT 필수 컬럼이 없습니다: {missing}"
        )

    result = pd.DataFrame()
    result[MUNICIPALITY_CODE_COLUMN] = df[GT_CODE_COLUMN].map(
        _normalize_municipality_code
    )
    result = result.loc[result[MUNICIPALITY_CODE_COLUMN].notna()].copy()

    lq_flag = pd.to_numeric(df.loc[result.index, GT_LQ_FLAG_COLUMN], errors="coerce")
    lq_flag = lq_flag.fillna(0.0).astype("float64")

    # 현재 GT의 jshis_flag는 1 또는 결측이지만, 잘못된 숫자가 들어오면 조기에 중단한다.
    invalid_flag = ~lq_flag.isin([0.0, 1.0])
    if invalid_flag.any():
        bad = result.loc[invalid_flag, MUNICIPALITY_CODE_COLUMN].tolist()
        raise ValueError(
            f"[{EVAL_LQ_SHEET_NAME}] jshis_flag는 0/1/결측만 허용합니다: {bad}"
        )

    result["gt_lq"] = lq_flag.astype("int64")

    # LF GT의 삿포로 10개 구를 모델 데이터의 삿포로시 한 행(01100)으로 맞춘다.
    ward_mask = result[MUNICIPALITY_CODE_COLUMN].isin(SAPPORO_WARD_CODES)
    result.loc[ward_mask, MUNICIPALITY_CODE_COLUMN] = SAPPORO_CITY_CODE

    # 삿포로처럼 여러 원본 행이 하나의 시정촌으로 합쳐진 경우 0/1 max로 집계한다.
    result = (
        result.groupby(MUNICIPALITY_CODE_COLUMN, as_index=False, sort=False)["gt_lq"]
        .max()
        .reset_index(drop=True)
    )

    return result


def _prepare_eval_ground_truth_df(gt_path: str | Path) -> pd.DataFrame:
    """LS/LQ GT를 시정촌코드 기준으로 합쳐 평가용 DataFrame을 만든다."""
    gt_path = Path(gt_path)
    if not gt_path.exists():
        raise FileNotFoundError(f"GT XLSX를 찾을 수 없습니다: {gt_path}")

    ls_df = _prepare_ls_ground_truth(gt_path)
    lq_df = _prepare_lq_ground_truth(gt_path)

    merged = ls_df.merge(
        lq_df,
        on=MUNICIPALITY_CODE_COLUMN,
        how="outer",
        validate="one_to_one",
        indicator=True,
    )

    unmatched = merged["_merge"].ne("both")
    if unmatched.any():
        problem_rows = merged.loc[
            unmatched, [MUNICIPALITY_CODE_COLUMN, "_merge"]
        ].to_dict("records")
        raise ValueError(
            "LS/LQ GT의 시정촌 목록이 서로 다릅니다: "
            f"{problem_rows[:10]}"
        )

    merged = merged.drop(columns="_merge")
    merged["event_idx"] = EVENT_TO_INDEX[EVAL_EVENT_NAME]
    return merged.reset_index(drop=True)


def load_eval_ground_truth(
    gt_path: str | Path,
    model_batch: PilotABatch,
) -> EvalGroundTruthBatch:
    """
    실제 GT를 읽고 전체 PilotABatch의 예측 행과 정확히 정렬해 eval 입력을 만든다.

    중요한 점:
    - GT는 현재 2018 훗카이도 이벤트에만 존재한다.
    - GT의 NaN/'NA'는 사용자가 확정한 규칙대로 0으로 변환한다.
    - 모델에서 실제 예측 가능한 행만 평가한다.
      따라서 GT에는 있지만 USGS/PGV 문제로 PilotABatch에서 제외된 시정촌은 eval에서도 제외된다.
    - model_row_idx를 함께 반환하므로 eval.py는 전체 posterior 결과에서 평가 행만 바로 선택할 수 있다.
    """
    model_batch.validate()
    gt_df = _prepare_eval_ground_truth_df(gt_path)

    eval_event_idx = EVENT_TO_INDEX[EVAL_EVENT_NAME]
    model_event_mask = model_batch.event_idx.eq(eval_event_idx)
    model_row_idx = torch.nonzero(model_event_mask, as_tuple=False).flatten()

    if model_row_idx.numel() == 0:
        raise ValueError(
            f"PilotABatch에 평가 이벤트 '{EVAL_EVENT_NAME}' 행이 없습니다."
        )

    # 전체 batch에서 2018 훗카이도에 해당하는 시정촌코드를 모델 행 순서 그대로 가져온다.
    model_codes = [
        model_batch.municipality_code[int(idx)]
        for idx in model_row_idx.tolist()
    ]

    if len(set(model_codes)) != len(model_codes):
        raise ValueError(
            f"'{EVAL_EVENT_NAME}' 모델 행에 중복 시정촌코드가 있습니다."
        )

    gt_by_code = gt_df.set_index(MUNICIPALITY_CODE_COLUMN)
    missing_gt_codes = [code for code in model_codes if code not in gt_by_code.index]
    if missing_gt_codes:
        raise ValueError(
            "모델에는 존재하지만 GT에 없는 평가 시정촌이 있습니다: "
            f"{missing_gt_codes}"
        )

    # model_codes 순서로 reindex하여 posterior와 GT가 같은 행 순서를 갖게 한다.
    aligned_gt = gt_by_code.loc[model_codes]

    eval_batch = EvalGroundTruthBatch(
        model_row_idx=model_row_idx.to(dtype=INDEX_DTYPE),
        gt_ls=torch.tensor(
            aligned_gt["gt_ls"].to_numpy(dtype="int64"),
            dtype=INDEX_DTYPE,
        ),
        gt_lq=torch.tensor(
            aligned_gt["gt_lq"].to_numpy(dtype="int64"),
            dtype=INDEX_DTYPE,
        ),
        event_idx=model_batch.event_idx[model_row_idx].clone(),
        municipality_code=tuple(model_codes),
    )

    eval_batch.validate()
    return eval_batch


def load_eval_inputs(
    stats_path: str | Path,
    usgs_path: str | Path,
    gt_path: str | Path,
    *,
    strict_expected_rows: bool = True,
) -> tuple[PilotABatch, EvalGroundTruthBatch]:
    """
    eval.py가 바로 사용할 모델 입력 + GT 입력을 함께 만든다.

    반환:
    - model_batch: 기존 학습/추론용 PilotABatch
    - eval_gt: 실제 GT가 존재하면서 모델 예측도 가능한 행만 정렬한 EvalGroundTruthBatch
    """
    model_batch = load_pilot_a_batch(
        stats_path,
        usgs_path,
        strict_expected_rows=strict_expected_rows,
    )
    eval_gt = load_eval_ground_truth(gt_path, model_batch)
    return model_batch, eval_gt


if __name__ == "__main__":
    # 아래 경로는 권장 프로젝트 구조 예시다. 실제 위치가 다르면 두 경로만 수정하면 된다.
    stats_file = Path("data/raw/재난프로젝트_시정촌별_통계데이터.xlsx")
    usgs_file = Path("data/raw/재난프로젝트_시정촌별_USGS.xlsx")

    batch = load_pilot_a_batch(stats_file, usgs_file)

    print("batch_size:", batch.batch_size)
    print("y:", tuple(batch.y.shape))
    print("E:", tuple(batch.E.shape))
    print("pgv:", tuple(batch.pgv.shape))
    print("pi_ls:", tuple(batch.pi_ls.shape))
    print("pi_lq:", tuple(batch.pi_lq.shape))
    print("event_idx:", tuple(batch.event_idx.shape))
    print("obs_mask:", tuple(batch.obs_mask.shape))
    print("municipality_code sample:", batch.municipality_code[:5])

    excluded = load_excluded_rows(stats_file, usgs_file)
    print("\n제외 행 수:", len(excluded))
    print(
        excluded[
            [MUNICIPALITY_CODE_COLUMN, "event", "exclude_reason"]
        ].to_string(index=False)
    )
