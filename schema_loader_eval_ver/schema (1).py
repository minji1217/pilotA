"""
Pilot A - data/schema.py

이 모듈은 실제 데이터를 읽거나 모델을 계산하지 않는다.
A/B가 공통으로 사용할 피해 채널 순서, 잠재상태 순서, 이벤트 index, 실제 XLSX 컬럼명,
dtype, 수치 안정화 상수, PilotABatch 구조와 검증 규칙을 정의한다.

중요: 시정촌코드는 계산용 숫자가 아니라 식별자(ID)이므로 5자리 문자열로 보존한다.
예: 아쓰마초 01581, 고리야마시 07203
"""

from __future__ import annotations

from dataclasses import dataclass

import torch
from torch import Tensor


# 피해 6채널 순서다. y, E, obs_mask의 두 번째 차원은 항상 이 순서를 따른다.
CHANNELS: tuple[str, ...] = (
    "death",
    "serious_injury",
    "minor_injury",
    "full_collapse",
    "half_collapse",
    "partial_damage",
)
NUM_CHANNELS: int = len(CHANNELS)

# 모델 내부 영어 채널명과 실제 통계 XLSX 한글 컬럼명을 연결한다.
DAMAGE_COLUMN_MAP: dict[str, str] = {
    "death": "사망",
    "serious_injury": "중상",
    "minor_injury": "경상",
    "full_collapse": "전파",
    "half_collapse": "반파",
    "partial_damage": "일부파손",
}

# 채널 이름으로 Tensor 내부 위치를 찾을 때 사용한다.
CHANNEL_TO_INDEX: dict[str, int] = {
    channel: index
    for index, channel in enumerate(CHANNELS)
}

# 피해 채널별 Exposure 원본 컬럼이다. 인명 3채널은 population, 주택 3채널은 households_general을 사용한다.
EXPOSURE_COLUMN_BY_CHANNEL: dict[str, str] = {
    "death": "population",
    "serious_injury": "population",
    "minor_injury": "population",
    "full_collapse": "households_general",
    "half_collapse": "households_general",
    "partial_damage": "households_general",
}

# 잠재상태 순서다. A의 log_L과 B의 log_w가 반드시 동일한 순서를 사용해야 한다.
LATENT_STATES: tuple[tuple[int, int], ...] = (
    (0, 0),
    (1, 0),
    (0, 1),
    (1, 1),
)
LATENT_STATE_NAMES: tuple[str, ...] = ("00", "10", "01", "11")
NUM_STATES: int = len(LATENT_STATES)

# 실제 두 XLSX의 이벤트 시트 순서다. event_idx는 0~7을 사용한다.
EVENTS: tuple[str, ...] = (
    "2004 니카타현주에쓰",
    "2007 니카타현주에쓰오키",
    "2008 이와테미야기",
    "2016 구마모토",
    "2018 오사카",
    "2018 훗카이도",
    "2021 후쿠시마",
    "2024 노토반도",
)
NUM_EVENTS: int = len(EVENTS)

EVENT_TO_INDEX: dict[str, int] = {
    event_name: index
    for index, event_name in enumerate(EVENTS)
}
INDEX_TO_EVENT: dict[int, str] = {
    index: event_name
    for index, event_name in enumerate(EVENTS)
}

# 현재 실제 파일 상태를 점검하기 위한 기대 행 수다. 모델 batch size를 고정하는 값은 아니다.
EXPECTED_NUM_STATS_ROWS: int = 403
EXPECTED_NUM_USGS_MATCHED_ROWS: int = 383
EXPECTED_NUM_MODEL_ROWS: int = 382

# 실제 XLSX에서 사용하는 공통 컬럼명이다.
MUNICIPALITY_CODE_COLUMN: str = "시정촌코드"
MUNICIPALITY_CODE_WIDTH: int = 5
PREFECTURE_COLUMN: str = "부현"
MUNICIPALITY_KO_COLUMN: str = "시정촌(한글)"
MUNICIPALITY_JA_COLUMN: str = "시정촌(日)"
POPULATION_COLUMN: str = "population"
HOUSEHOLDS_COLUMN: str = "households_general"

# 이번 Pilot은 최대 prior가 아니라 평균 prior를 사용한다.
USGS_LS_PRIOR_COLUMN: str = "LS_prior(평균)"
USGS_LQ_PRIOR_COLUMN: str = "LQ_prior(평균)"
USGS_PGV_COLUMN: str = "PGV"

# 첫 구현에서는 확률/우도 계산의 수치 안정성을 위해 float64를 사용한다.
DTYPE: torch.dtype = torch.float64

# event_idx처럼 실제 Tensor index로 쓰는 값은 정수형으로 관리한다.
INDEX_DTYPE: torch.dtype = torch.long

# B의 prior.py에서 logit(pi)를 계산하기 전에 torch.clamp(pi, EPS, 1-EPS)를 적용한다.
EPS: float = 1e-6


@dataclass
class PilotABatch:
    """
    loader.py가 만든 A/B 공통 입력 데이터.

    y: [B,6] float64, 피해 건수
    E: [B,6] float64, 채널별 Exposure
    pgv: [B] float64, USGS PGV
    pi_ls: [B] float64, LS_prior(평균)
    pi_lq: [B] float64, LQ_prior(평균)
    event_idx: [B] long, 이벤트 index 0~7
    obs_mask: [B,6] bool, 피해 채널별 관측 여부
    municipality_code: 길이 B의 5자리 문자열 tuple, 결과 추적과 join 식별용 메타데이터

    시정촌코드는 모델 계산용 Tensor가 아니다.
    예: 1581을 int로 보관하면 앞의 0이 사라지므로 반드시 "01581"처럼 문자열로 보존한다.
    """

    y: Tensor
    E: Tensor
    pgv: Tensor
    pi_ls: Tensor
    pi_lq: Tensor
    event_idx: Tensor
    obs_mask: Tensor
    municipality_code: tuple[str, ...]

    @property
    def batch_size(self) -> int:
        """
        현재 batch의 행 수를 반환한다.

        입력: 없음
        출력: int
        예: y.shape == [382,6]이면 382를 반환한다.
        이유: B=382를 하드코딩하지 않고 실제 Tensor 크기를 기준으로 계산하기 위해서다.
        """
        return int(self.y.shape[0])

    def validate(self) -> None:
        """
        PilotABatch가 schema 규칙을 만족하는지 검사한다.

        입력: 없음
        출력: 정상일 경우 None, 문제가 있으면 ValueError 또는 TypeError
        역할: loader에서 잘못 만든 데이터가 regression/prior까지 넘어가기 전에 즉시 발견한다.
        """
        B = self.batch_size
        if B <= 0:
            raise ValueError("batch에는 최소 1개 이상의 행이 있어야 합니다.")

        # y, E, obs_mask는 모두 [B,6]이어야 같은 행·같은 채널끼리 대응한다.
        expected_matrix_shape = (B, NUM_CHANNELS)
        for name, tensor in {
            "y": self.y,
            "E": self.E,
            "obs_mask": self.obs_mask,
        }.items():
            if tuple(tensor.shape) != expected_matrix_shape:
                raise ValueError(
                    f"{name} shape 오류: expected={expected_matrix_shape}, actual={tuple(tensor.shape)}"
                )

        # PGV, prior, event_idx는 시정촌×이벤트 행마다 값 하나이므로 [B]여야 한다.
        expected_vector_shape = (B,)
        for name, tensor in {
            "pgv": self.pgv,
            "pi_ls": self.pi_ls,
            "pi_lq": self.pi_lq,
            "event_idx": self.event_idx,
        }.items():
            if tuple(tensor.shape) != expected_vector_shape:
                raise ValueError(
                    f"{name} shape 오류: expected={expected_vector_shape}, actual={tuple(tensor.shape)}"
                )

        # 시정촌코드는 Tensor가 아니라 길이 B의 5자리 문자열 메타데이터다.
        if len(self.municipality_code) != B:
            raise ValueError(
                f"municipality_code 길이 오류: expected={B}, actual={len(self.municipality_code)}"
            )

        invalid_codes = [
            code
            for code in self.municipality_code
            if not isinstance(code, str)
            or len(code) != MUNICIPALITY_CODE_WIDTH
            or not code.isdigit()
        ]
        if invalid_codes:
            raise ValueError(
                "municipality_code는 앞자리 0을 포함한 5자리 숫자 문자열이어야 합니다. "
                f"잘못된 예={invalid_codes[:5]}"
            )

        # 모델의 연속값 Tensor는 모두 같은 float64 dtype을 사용한다.
        float_tensors = {
            "y": self.y,
            "E": self.E,
            "pgv": self.pgv,
            "pi_ls": self.pi_ls,
            "pi_lq": self.pi_lq,
        }
        for name, tensor in float_tensors.items():
            if tensor.dtype != DTYPE:
                raise TypeError(
                    f"{name} dtype 오류: expected={DTYPE}, actual={tensor.dtype}"
                )

        if self.obs_mask.dtype != torch.bool:
            raise TypeError("obs_mask는 torch.bool dtype이어야 합니다.")

        if self.event_idx.dtype != INDEX_DTYPE:
            raise TypeError(
                f"event_idx dtype 오류: expected={INDEX_DTYPE}, actual={self.event_idx.dtype}"
            )

        # NaN/Inf가 모델에 들어가면 loss가 NaN이 될 수 있으므로 미리 차단한다.
        for name, tensor in float_tensors.items():
            if not torch.isfinite(tensor).all():
                raise ValueError(f"{name}에 NaN 또는 Inf가 존재합니다.")

        # 피해 건수는 음수가 될 수 없다.
        if (self.y < 0).any():
            raise ValueError("y에는 음수 피해 건수가 존재할 수 없습니다.")

        # y dtype은 float64지만 실제 관측값은 count이므로 정수 형태여야 한다.
        observed_y = self.y[self.obs_mask]
        if not torch.allclose(observed_y, observed_y.round()):
            raise ValueError("관측된 y는 피해 건수이므로 정수 값이어야 합니다.")

        # 결측 채널은 loader에서 y=0 placeholder, obs_mask=False로 통일한다.
        missing_y = self.y[~self.obs_mask]
        if missing_y.numel() > 0 and (missing_y != 0).any():
            raise ValueError("결측 채널의 y placeholder는 0이어야 합니다.")

        # 현재 회귀식의 Exposure는 양수여야 한다.
        if (self.E <= 0).any():
            raise ValueError("E(exposure)는 모든 채널에서 0보다 커야 합니다.")

        # regression.py에서 log(PGV)를 사용하므로 PGV는 0보다 커야 한다.
        if (self.pgv <= 0).any():
            raise ValueError("PGV는 반드시 0보다 커야 합니다.")

        # prior는 확률이므로 [0,1] 범위여야 한다. 0과 1은 여기서는 허용하고 prior.py에서 clamp한다.
        if ((self.pi_ls < 0) | (self.pi_ls > 1)).any():
            raise ValueError("pi_ls는 [0,1] 범위여야 합니다.")
        if ((self.pi_lq < 0) | (self.pi_lq > 1)).any():
            raise ValueError("pi_lq는 [0,1] 범위여야 합니다.")

        # 이벤트가 8개이므로 event_idx는 0~7이어야 한다.
        invalid_event = (self.event_idx < 0) | (self.event_idx >= NUM_EVENTS)
        if invalid_event.any():
            raise ValueError(f"event_idx는 0~{NUM_EVENTS - 1} 범위여야 합니다.")


@dataclass
class EvalGroundTruthBatch:
    """
    eval.py가 사용할 실제 GT 정답 데이터.

    현재 GT 파일(LS_LF 데이터자료.xlsx)은 2018 훗카이도 이벤트에 대한 LS/LQ 정답을 제공한다.
    loader.py가 GT를 읽은 뒤 실제 모델 batch와 시정촌코드를 맞춰 이 구조를 만든다.

    model_row_idx: [B_eval] long, 전체 PilotABatch에서 같은 시정촌 행의 위치
    gt_ls: [B_eval] long, 산사태 GT(0/1)
    gt_lq: [B_eval] long, 액상화 GT(0/1)
    event_idx: [B_eval] long, 평가 이벤트 index
    municipality_code: 길이 B_eval의 5자리 문자열 tuple

    예:
        posterior_ls가 전체 382행 결과라면
        posterior_ls[eval_gt.model_row_idx]로 GT가 존재하는 평가 행만 선택할 수 있다.
    """

    model_row_idx: Tensor
    gt_ls: Tensor
    gt_lq: Tensor
    event_idx: Tensor
    municipality_code: tuple[str, ...]

    @property
    def batch_size(self) -> int:
        """현재 평가 가능한 GT 행 수를 반환한다."""
        return int(self.gt_ls.shape[0])

    @property
    def gt_state_idx(self) -> Tensor:
        """
        (LS, LQ) GT를 schema.py의 잠재상태 순서 00/10/01/11에 맞는 index로 반환한다.

        00 -> 0
        10 -> 1
        01 -> 2
        11 -> 3
        """
        return self.gt_ls + (2 * self.gt_lq)

    def validate(self) -> None:
        """eval 입력이 shape/dtype/라벨 규칙을 만족하는지 검사한다."""
        B = self.batch_size
        if B <= 0:
            raise ValueError("eval GT에는 최소 1개 이상의 행이 있어야 합니다.")

        expected_shape = (B,)
        for name, tensor in {
            "model_row_idx": self.model_row_idx,
            "gt_ls": self.gt_ls,
            "gt_lq": self.gt_lq,
            "event_idx": self.event_idx,
        }.items():
            if tuple(tensor.shape) != expected_shape:
                raise ValueError(
                    f"{name} shape 오류: expected={expected_shape}, actual={tuple(tensor.shape)}"
                )
            if tensor.dtype != INDEX_DTYPE:
                raise TypeError(
                    f"{name} dtype 오류: expected={INDEX_DTYPE}, actual={tensor.dtype}"
                )

        if (self.model_row_idx < 0).any():
            raise ValueError("model_row_idx에는 음수 index가 올 수 없습니다.")
        if self.model_row_idx.unique().numel() != B:
            raise ValueError("model_row_idx에 중복 행이 존재합니다.")

        for name, tensor in {"gt_ls": self.gt_ls, "gt_lq": self.gt_lq}.items():
            if ((tensor != 0) & (tensor != 1)).any():
                raise ValueError(f"{name}는 0 또는 1만 가져야 합니다.")

        invalid_event = (self.event_idx < 0) | (self.event_idx >= NUM_EVENTS)
        if invalid_event.any():
            raise ValueError(f"event_idx는 0~{NUM_EVENTS - 1} 범위여야 합니다.")

        if len(self.municipality_code) != B:
            raise ValueError(
                f"municipality_code 길이 오류: expected={B}, actual={len(self.municipality_code)}"
            )

        invalid_codes = [
            code
            for code in self.municipality_code
            if not isinstance(code, str)
            or len(code) != MUNICIPALITY_CODE_WIDTH
            or not code.isdigit()
        ]
        if invalid_codes:
            raise ValueError(
                "eval municipality_code는 5자리 숫자 문자열이어야 합니다. "
                f"잘못된 예={invalid_codes[:5]}"
            )
