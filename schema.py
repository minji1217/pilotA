"""
Pilot A - data/schema.py

이 모듈은 실제 데이터를 읽거나 모델을 계산하지 않는다.
A/B가 공통으로 사용할 피해 채널 순서, 잠재상태 순서, 이벤트 index,
실제 XLSX 컬럼명, dtype, 수치 안정화 상수,
PilotABatch 구조와 검증 규칙을 정의한다.

중요:
시정촌코드는 계산용 숫자가 아니라 식별자(ID)이므로
5자리 문자열로 보존한다.

예:
아쓰마초 01581
고리야마시 07203
"""

from __future__ import annotations

from dataclasses import dataclass

import torch
from torch import Tensor


# ============================================================
# 1. 피해 채널
# ============================================================

# 피해 6채널 순서다.
# y, E, obs_mask의 두 번째 차원은 항상 이 순서를 따른다.
CHANNELS: tuple[str, ...] = (
    "death",
    "serious_injury",
    "minor_injury",
    "full_collapse",
    "half_collapse",
    "partial_damage",
)

NUM_CHANNELS: int = len(CHANNELS)


# 모델 내부 영어 채널명과
# 실제 통계 XLSX 한글 컬럼명을 연결한다.
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


# ============================================================
# 2. Exposure
# ============================================================

# 피해 채널별 Exposure 원본 컬럼이다.
#
# 인명 피해 3채널
#   death
#   serious_injury
#   minor_injury
# → population 사용
#
# 주택 피해 3채널
#   full_collapse
#   half_collapse
#   partial_damage
# → households_general 사용
EXPOSURE_COLUMN_BY_CHANNEL: dict[str, str] = {
    "death": "population",
    "serious_injury": "population",
    "minor_injury": "population",
    "full_collapse": "households_general",
    "half_collapse": "households_general",
    "partial_damage": "households_general",
}


# ============================================================
# 3. 잠재 상태
# ============================================================

# 잠재상태 순서다.
#
# A의 log_L과
# B의 log_w가 반드시 동일한 순서를 사용해야 한다.
#
# (LS, LQ)
#
# 00 = LS 없음 / LQ 없음
# 10 = LS 있음 / LQ 없음
# 01 = LS 없음 / LQ 있음
# 11 = LS 있음 / LQ 있음
LATENT_STATES: tuple[tuple[int, int], ...] = (
    (0, 0),
    (1, 0),
    (0, 1),
    (1, 1),
)

LATENT_STATE_NAMES: tuple[str, ...] = (
    "00",
    "10",
    "01",
    "11",
)

NUM_STATES: int = len(LATENT_STATES)


# ============================================================
# 4. 이벤트
# ============================================================

# 실제 두 XLSX의 이벤트 시트 순서다.
#
# 기존 event_idx 0~7의 의미와 reference_event_idx=0(2004 니가타)을
# 보존하기 위해 새로 추가된 2000 돗토리는 맨 뒤 index 8에 둔다.
EVENTS: tuple[str, ...] = (
    "2004 니가타현주에쓰",
    "2007 니가타현주에쓰오키",
    "2008 이와테미야기",
    "2016 구마모토",
    "2018 오사카",
    "2018 훗카이도",
    "2021 후쿠시마",
    "2024 노토반도",
    "2000 돗토리",
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


# ============================================================
# 5. 실제 파일 행 수 검증용 상수
# ============================================================

# 현재 실제 파일 상태를 점검하기 위한 기대 행 수다.
#
# 모델 batch size를 특정 값으로 고정하는 용도가 아니라
# 현재 실제 파일 상태가 예상과 맞는지 점검하기 위한 값이다.
#
# 최신 실제 자료:
#
# 통계 원본             439행
# USGS 존재/매칭        419행
# 최종 모델 사용        418행
EXPECTED_NUM_STATS_ROWS: int = 439
EXPECTED_NUM_USGS_MATCHED_ROWS: int = 419
EXPECTED_NUM_MODEL_ROWS: int = 418


# ============================================================
# 6. 실제 XLSX 컬럼명
# ============================================================

MUNICIPALITY_CODE_COLUMN: str = "시정촌코드"
MUNICIPALITY_CODE_WIDTH: int = 5

PREFECTURE_COLUMN: str = "부현"
MUNICIPALITY_KO_COLUMN: str = "시정촌(한글)"
MUNICIPALITY_JA_COLUMN: str = "시정촌(日)"

POPULATION_COLUMN: str = "population"
HOUSEHOLDS_COLUMN: str = "households_general"


# ============================================================
# 7. USGS 컬럼명
# ============================================================

# 이번 Pilot은 최대 prior가 아니라 평균 prior를 사용한다.
USGS_LS_PRIOR_COLUMN: str = "LS_prior(평균)"
USGS_LQ_PRIOR_COLUMN: str = "LQ_prior(평균)"
USGS_PGV_COLUMN: str = "PGV"


# ============================================================
# 8. Tensor dtype
# ============================================================

# 첫 구현에서는 확률/우도 계산의 수치 안정성을 위해 float64 사용
DTYPE: torch.dtype = torch.float64

# event_idx처럼 Tensor index로 사용하는 값은 정수형
INDEX_DTYPE: torch.dtype = torch.long


# ============================================================
# 9. 수치 안정화 상수
# ============================================================

# B의 prior.py에서
#
# logit(pi)
#
# 계산 전에
#
# torch.clamp(pi, EPS, 1-EPS)
#
# 를 적용한다.
EPS: float = 1e-6


# ============================================================
# 10. 모델 학습/추론용 Batch
# ============================================================

@dataclass
class PilotABatch:
    """
    loader.py가 만든 A/B 공통 모델 입력 데이터.

    ----------------------------------------------------------
    Tensor 구조
    ----------------------------------------------------------

    y
        [B, 6] float64
        실제 피해 건수

    E
        [B, 6] float64
        채널별 Exposure

    pgv
        [B] float64
        USGS PGV

    pi_ls
        [B] float64
        LS_prior(평균)

    pi_lq
        [B] float64
        LQ_prior(평균)

    event_idx
        [B] long
        이벤트 index 0~8

    obs_mask
        [B, 6] bool
        피해 채널별 실제 관측 여부

        True
            실제 피해값이 존재

        False
            결측
            이 경우 y에는 계산용 placeholder 0이 저장됨

    municipality_code
        길이 B의 5자리 문자열 tuple

        모델 계산용 Tensor가 아니라
        결과 추적 / join을 위한 식별자 메타데이터

    ----------------------------------------------------------
    예
    ----------------------------------------------------------

    아쓰마초:

        municipality_code = "01581"

    1581을 int로 그대로 저장하면 앞의 0이 사라지므로
    반드시 문자열로 보존한다.
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

        예:
            y.shape == [B, 6]

        이면:

            batch_size == B

        특정 행 수를 하드코딩하지 않고
        실제 Tensor 크기를 기준으로 계산한다.
        """
        return int(self.y.shape[0])


    def validate(self) -> None:
        """
        PilotABatch가 schema 규칙을 만족하는지 검사한다.

        정상:
            None 반환

        문제:
            ValueError 또는 TypeError 발생

        목적:
            loader에서 잘못 만든 데이터가
            regression / likelihood / prior까지 넘어가기 전에
            즉시 발견한다.
        """

        B = self.batch_size

        if B <= 0:
            raise ValueError(
                "batch에는 최소 1개 이상의 행이 있어야 합니다."
            )


        # ----------------------------------------------------
        # y / E / obs_mask shape 검사
        # ----------------------------------------------------

        # 모두 [B,6]이어야
        # 같은 행 × 같은 채널끼리 대응한다.
        expected_matrix_shape = (
            B,
            NUM_CHANNELS,
        )

        for name, tensor in {
            "y": self.y,
            "E": self.E,
            "obs_mask": self.obs_mask,
        }.items():

            if tuple(tensor.shape) != expected_matrix_shape:
                raise ValueError(
                    f"{name} shape 오류: "
                    f"expected={expected_matrix_shape}, "
                    f"actual={tuple(tensor.shape)}"
                )


        # ----------------------------------------------------
        # PGV / prior / event_idx shape 검사
        # ----------------------------------------------------

        # PGV, prior, event_idx는
        # 시정촌×이벤트 행마다 값 하나이므로 [B]
        expected_vector_shape = (B,)

        for name, tensor in {
            "pgv": self.pgv,
            "pi_ls": self.pi_ls,
            "pi_lq": self.pi_lq,
            "event_idx": self.event_idx,
        }.items():

            if tuple(tensor.shape) != expected_vector_shape:
                raise ValueError(
                    f"{name} shape 오류: "
                    f"expected={expected_vector_shape}, "
                    f"actual={tuple(tensor.shape)}"
                )


        # ----------------------------------------------------
        # municipality_code 검사
        # ----------------------------------------------------

        if len(self.municipality_code) != B:
            raise ValueError(
                "municipality_code 길이 오류: "
                f"expected={B}, "
                f"actual={len(self.municipality_code)}"
            )

        invalid_codes = [
            code
            for code in self.municipality_code
            if (
                not isinstance(code, str)
                or len(code) != MUNICIPALITY_CODE_WIDTH
                or not code.isdigit()
            )
        ]

        if invalid_codes:
            raise ValueError(
                "municipality_code는 앞자리 0을 포함한 "
                "5자리 숫자 문자열이어야 합니다. "
                f"잘못된 예={invalid_codes[:5]}"
            )


        # ----------------------------------------------------
        # float Tensor dtype 검사
        # ----------------------------------------------------

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
                    f"{name} dtype 오류: "
                    f"expected={DTYPE}, "
                    f"actual={tensor.dtype}"
                )


        # ----------------------------------------------------
        # obs_mask dtype
        # ----------------------------------------------------

        if self.obs_mask.dtype != torch.bool:
            raise TypeError(
                "obs_mask는 torch.bool dtype이어야 합니다."
            )


        # ----------------------------------------------------
        # event_idx dtype
        # ----------------------------------------------------

        if self.event_idx.dtype != INDEX_DTYPE:
            raise TypeError(
                f"event_idx dtype 오류: "
                f"expected={INDEX_DTYPE}, "
                f"actual={self.event_idx.dtype}"
            )


        # ----------------------------------------------------
        # NaN / Inf 검사
        # ----------------------------------------------------

        # 모델에 NaN/Inf가 들어가면
        # loss 전체가 NaN이 될 수 있으므로 미리 차단한다.
        for name, tensor in float_tensors.items():

            if not torch.isfinite(tensor).all():
                raise ValueError(
                    f"{name}에 NaN 또는 Inf가 존재합니다."
                )


        # ----------------------------------------------------
        # y 검증
        # ----------------------------------------------------

        # 피해 건수는 음수가 될 수 없다.
        if (self.y < 0).any():
            raise ValueError(
                "y에는 음수 피해 건수가 존재할 수 없습니다."
            )


        # y Tensor는 float64이지만
        # 실제 관측 피해는 count이므로 정수 형태여야 한다.
        observed_y = self.y[self.obs_mask]

        if not torch.allclose(
            observed_y,
            observed_y.round(),
        ):
            raise ValueError(
                "관측된 y는 피해 건수이므로 "
                "정수 값이어야 합니다."
            )


        # 결측 피해 채널은
        #
        # y = 0 placeholder
        # obs_mask = False
        #
        # 로 통일한다.
        missing_y = self.y[~self.obs_mask]

        if (
            missing_y.numel() > 0
            and (missing_y != 0).any()
        ):
            raise ValueError(
                "결측 채널의 y placeholder는 "
                "0이어야 합니다."
            )


        # ----------------------------------------------------
        # Exposure 검증
        # ----------------------------------------------------

        # 현재 회귀식에서는
        # Exposure가 모든 채널에서 양수여야 한다.
        if (self.E <= 0).any():
            raise ValueError(
                "E(exposure)는 모든 채널에서 "
                "0보다 커야 합니다."
            )


        # ----------------------------------------------------
        # PGV 검증
        # ----------------------------------------------------

        # regression.py에서 log(PGV)를 사용하므로
        # PGV > 0 이어야 한다.
        if (self.pgv <= 0).any():
            raise ValueError(
                "PGV는 반드시 0보다 커야 합니다."
            )


        # ----------------------------------------------------
        # prior 검증
        # ----------------------------------------------------

        # prior는 확률이므로 [0,1] 범위
        #
        # 0과 1 자체는 여기서는 허용한다.
        # prior.py에서 logit 계산 직전에 clamp한다.
        if (
            (self.pi_ls < 0)
            | (self.pi_ls > 1)
        ).any():
            raise ValueError(
                "pi_ls는 [0,1] 범위여야 합니다."
            )

        if (
            (self.pi_lq < 0)
            | (self.pi_lq > 1)
        ).any():
            raise ValueError(
                "pi_lq는 [0,1] 범위여야 합니다."
            )


        # ----------------------------------------------------
        # event_idx 검증
        # ----------------------------------------------------

        invalid_event = (
            (self.event_idx < 0)
            | (self.event_idx >= NUM_EVENTS)
        )

        if invalid_event.any():
            raise ValueError(
                f"event_idx는 0~{NUM_EVENTS - 1} "
                "범위여야 합니다."
            )


# ============================================================
# 11. 평가용 Ground Truth Batch
# ============================================================

@dataclass
class EvalGroundTruthBatch:
    """
    eval.py가 사용할 실제 GT 정답 데이터.

    현재 GT 파일:
        LS_LF 데이터자료.xlsx

    평가 대상:
        GT가 준비된 여러 이벤트


    ----------------------------------------------------------
    구조
    ----------------------------------------------------------

    model_row_idx
        [B_eval] long

        전체 PilotABatch에서
        해당 평가 시정촌이 위치한 행 index

        예:
            전체 posterior_ls [B_model]

            posterior_ls[
                eval_gt.model_row_idx
            ]

        로 평가 이벤트의 posterior만 뽑을 수 있다.


    gt_ls
        [B_eval] long

        산사태 GT 0/1

        확정 규칙:

            ls_flag 컬럼이 있으면 ls_flag를 우선 사용
                1  → 1
                0  → 0
                NA → Tensor에는 placeholder 0
                     ls_eval_mask=False

            ls_flag 컬럼이 없으면 ls_area_ha 사용
                > 0 → 1
                = 0 → 0
                NA  → Tensor에는 placeholder 0
                      ls_eval_mask=False
                < 0 → 데이터 오류


    gt_lq
        [B_eval] long

        액상화 GT 0/1

        확정 규칙:

            jshis_flag 컬럼이 있으면 우선 사용
                1  → 1
                0  → 0
                NA → 0, lq_eval_mask=True

            jshis_flag가 없으면 lq_flag 사용
                1  → 1
                0  → 0
                NA → Tensor에는 placeholder 0
                     lq_eval_mask=False


    ls_eval_mask
        [B_eval] bool

        True
            LS GT가 0/1로 확정되어 LS 평가에 사용

        False
            LS 원본이 NA
            → gt_ls의 placeholder 0은 평가에 사용하지 않음


    lq_eval_mask
        [B_eval] bool

        True
            LQ GT가 0/1로 확정되어 LQ 평가에 사용
            jshis_flag의 NA는 규칙상 0으로 확정되므로 True

        False
            일반 lq_flag가 NA
            → gt_lq의 placeholder 0은 평가에 사용하지 않음


    event_idx
        [B_eval] long

        평가 이벤트 index


    municipality_code
        길이 B_eval의 5자리 문자열 tuple
    """

    model_row_idx: Tensor

    gt_ls: Tensor
    gt_lq: Tensor

    # False이면 LS 원본이 NA이므로 LS 성능평가에서 제외한다.
    ls_eval_mask: Tensor

    # False이면 일반 lq_flag 원본이 NA이므로 LQ 성능평가에서 제외한다.
    # jshis_flag의 NA는 0으로 확정되므로 True다.
    lq_eval_mask: Tensor

    event_idx: Tensor

    municipality_code: tuple[str, ...]


    @property
    def batch_size(self) -> int:
        """
        현재 평가용 GT 행 수를 반환한다.

        주의:
        LS/LQ에서 실제 평가 가능한 행 수와는 다를 수 있다.

        실제 평가 행 수는:

            LS    = self.ls_eval_mask.sum()
            LQ    = self.lq_eval_mask.sum()
            Joint = (self.ls_eval_mask & self.lq_eval_mask).sum()

        으로 확인한다.
        """
        return int(self.gt_ls.shape[0])


    @property
    def gt_state_idx(self) -> Tensor:
        """
        (LS, LQ) GT를 잠재상태 index로 변환한다.

        LATENT_STATES 순서:

            00 -> 0
            10 -> 1
            01 -> 2
            11 -> 3

        계산:

            gt_state_idx
            = gt_ls + 2 * gt_lq

        예:

            gt_ls=1
            gt_lq=0

            → 1 + 2*0
            → 1
            → 상태10


        주의:
        LS 또는 LQ가 NA인 행에는 Tensor 저장을 위한 placeholder 0이
        들어갈 수 있다.

        따라서 joint state 평가 시에는 반드시

            ls_eval_mask & lq_eval_mask

        가 True인 행만 사용해야 한다.
        """

        return self.gt_ls + (2 * self.gt_lq)


    def validate(self) -> None:
        """
        eval 입력이
        shape / dtype / 라벨 규칙을 만족하는지 검사한다.
        """

        B = self.batch_size

        if B <= 0:
            raise ValueError(
                "eval GT에는 최소 1개 이상의 "
                "행이 있어야 합니다."
            )


        expected_shape = (B,)


        # ----------------------------------------------------
        # 정수형 Tensor shape / dtype 검사
        # ----------------------------------------------------

        for name, tensor in {
            "model_row_idx": self.model_row_idx,
            "gt_ls": self.gt_ls,
            "gt_lq": self.gt_lq,
            "event_idx": self.event_idx,
        }.items():

            if tuple(tensor.shape) != expected_shape:
                raise ValueError(
                    f"{name} shape 오류: "
                    f"expected={expected_shape}, "
                    f"actual={tuple(tensor.shape)}"
                )

            if tensor.dtype != INDEX_DTYPE:
                raise TypeError(
                    f"{name} dtype 오류: "
                    f"expected={INDEX_DTYPE}, "
                    f"actual={tensor.dtype}"
                )


        # ----------------------------------------------------
        # LS / LQ 평가 mask 검사
        # ----------------------------------------------------

        for name, mask in {
            "ls_eval_mask": self.ls_eval_mask,
            "lq_eval_mask": self.lq_eval_mask,
        }.items():

            if tuple(mask.shape) != expected_shape:
                raise ValueError(
                    f"{name} shape 오류: "
                    f"expected={expected_shape}, "
                    f"actual={tuple(mask.shape)}"
                )

            if mask.dtype != torch.bool:
                raise TypeError(
                    f"{name} dtype 오류: "
                    f"expected={torch.bool}, "
                    f"actual={mask.dtype}"
                )


        # ----------------------------------------------------
        # model_row_idx 검사
        # ----------------------------------------------------

        if (self.model_row_idx < 0).any():
            raise ValueError(
                "model_row_idx에는 음수 index가 "
                "올 수 없습니다."
            )

        if self.model_row_idx.unique().numel() != B:
            raise ValueError(
                "model_row_idx에 중복 행이 존재합니다."
            )


        # ----------------------------------------------------
        # GT 라벨 검사
        # ----------------------------------------------------

        # LS/LQ의 평가 제외 위치에는 placeholder 0이 들어갈 수 있으므로
        # Tensor 자체에는 여전히 0/1만 존재한다.
        for name, tensor in {
            "gt_ls": self.gt_ls,
            "gt_lq": self.gt_lq,
        }.items():

            invalid_label = (
                (tensor != 0)
                & (tensor != 1)
            )

            if invalid_label.any():
                raise ValueError(
                    f"{name}는 0 또는 1만 "
                    "가져야 합니다."
                )


        # ----------------------------------------------------
        # event index 검사
        # ----------------------------------------------------

        invalid_event = (
            (self.event_idx < 0)
            | (self.event_idx >= NUM_EVENTS)
        )

        if invalid_event.any():
            raise ValueError(
                f"event_idx는 0~{NUM_EVENTS - 1} "
                "범위여야 합니다."
            )


        # ----------------------------------------------------
        # 시정촌코드 검사
        # ----------------------------------------------------

        if len(self.municipality_code) != B:
            raise ValueError(
                "municipality_code 길이 오류: "
                f"expected={B}, "
                f"actual={len(self.municipality_code)}"
            )

        invalid_codes = [
            code
            for code in self.municipality_code
            if (
                not isinstance(code, str)
                or len(code) != MUNICIPALITY_CODE_WIDTH
                or not code.isdigit()
            )
        ]

        if invalid_codes:
            raise ValueError(
                "eval municipality_code는 "
                "5자리 숫자 문자열이어야 합니다. "
                f"잘못된 예={invalid_codes[:5]}"
            )