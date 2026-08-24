"""
pilot A - 공통 데이터 스키마 정의
A와 B가 개발할 때 사용하는 "공통 약속" 한 곳에 정의

예를 들어,

- 피해 채널은 어떤 순서인가?
- 잠재상태 4개는 어떤 순서인가?
- 이벤트 8개는 어떤 index를 사용하는가?
- Excel의 어떤 컬럼을 사용할 것인가?
- USGS prior는 평균/최대 중 어떤 컬럼을 사용할 것인가?
- loader.py가 최종적으로 어떤 tensor들을 만들어야 하는가?
- 각 tensor의 shape과 dtype은 무엇인가?

를 여기서 고정한다.

전체 흐름
---------

통계 XLSX + USGS XLSX
        ↓
    loader.py
        ↓
   PilotABatch
        ↓
 ┌──────────────┐
 │              │
A              B
regression     prior
likelihood     marginal/train/infer
"""

from __future__ import annotations

from dataclasses import dataclass

import torch
from torch import Tensor

# 1. 피해 채널 정의
"""
모델에서 사용하는 피해 채널은 총 6개 
사망 중상 경상 전파 반파 일부파손

실제 아쓰마초 피해가 
    사망       36
    중상        0
    경상       61
    전파      224
    반파      318
    일부파손 1097

이라면 모델에서는

    y = [36, 0, 61, 224, 318, 1097]

이라는 숫자 배열로 바뀐다.
"""
CHANNELS: tuple[str, ...] = (
    "death",
    "serious_injury",
    "minor_injury",
    "full_collapse",
    "half_collapse",
    "partial_damage"
)

NUM_CHANNELS: int = len(CHANNELS)

# 영어 모델 채널명 -> 실제 통계 xlsx 컬럼명
# loader.py에서 excel 데이터 읽을 때 사용
# 예 : 
# DAMAGE_COLUMN_MAP["death"] -> 사망
DAMAGE_COLUMN_MAP: dict[str, str] = {
    "death": "사망",
    "serious_injury": "중상",
    "minor_injury": "경상",
    "full_collapse": "전파",
    "half_collapse": "반파",
    "partial_damage": "일부파손",
}


# 채널 이름으로 tensor 내부 idx 찾고 싶을 때 사용
# 예:
# CHANNEL_TO_INDEX["death"]
# -> 0
# CHANNEL_TO_INDEX["partial_damage"]
# -> 5

CHANNEL_TO_INDEX : dict[str, int] = {
    channel: index for index, channel in enumerate(CHANNELS)
}


# 2. E 규칙
# E는 해당 피해가 발생할 수 있는 전체 대상 수 
"""

Pilot A에서는:

인명 피해
    사망
    중상
    경상

→ population 사용


주택 피해
    전파
    반파
    일부파손

→ households_general 사용


예를 들어 아쓰마초가

    population = 4838
    households_general = 2121

이라면:

    E = [
        4838, 4838, 4838,
        2121, 2121, 2121
    ]

이 된다.

이 규칙 자체는 schema.py에 정의하고,
실제 E Tensor를 만드는 작업은 loader.py가 담당한다.
"""

EXPOSURE_COLUMN_BY_CHANNEL: dict[str, str] = {
    "death": "population",
    "serious_injury": "population",
    "minor_injury" : "population",
    "full_collapse": "households_general",
    "half_collapse": "households_general",
    "partial_damage": "households_general",
}

# 3. 잠재상태 4개 정의
LATENT_STATES: tuple[tuple[int, int], ...]=(
    (0,0), (1,0), (0,1), (1,1)
)

NUM_STATES: int = len(LATENT_STATES)

# 상태 이름은 로그 출력이나 디버깅할 때 사용하기 위한 값임
LATENT_STATE_NAMES: tuple[str, ...]=(
    "00","10","01","11"
)

# 4. 지진 이벤트 정의
"""
loader.py에서는 각 이벤트 문자열을
모델에서 사용하기 편한 정수 event_idx로 바꾼다.

예:

    "2004 니카타현주에쓰"
        -> event_idx = 0

    "2018 훗카이도"
        -> event_idx = 5

    "2024 노토반도"
        -> event_idx = 7
"""

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


# 반대로 event_idx에서 이벤트 이름 찾을 때 사용하기 위함
# 예 : 
# INDEX_TO_EVENT[5] -> "2018 훗카이도"
INDEX_TO_EVENT: dict[int, str] = {
    index: event_name
    for index, event_name in enumerate(EVENTS)
}

# 실제 데이터 행 수 
"""
원본 시정촌 x 이벤트 데이터 = 총 403행
-> 피해 y, Exposure E, PGV, LS/LQ prior 모두 존재하는 행이 필요 
-> 이때, 현재 모델 입력으로 사용하기로 한 행은 383행 
"""

EXPECTED_NUM_STATS_ROWS: int = 403

EXPECTED_NUM_MODEL_ROWS: int = 383

# 원본 XLSX에서 사용하는 공통 컬럼명
""" 
통계 XLSX와 USGS XLSX joing시 가장 중요한 식별자가 시정촌 코드 
-> 이때 동일 시정촌이 서로 다른 지진 이벤트에 등장 가능하기에 event+시정촌코드 조합으로 행 구분
"""
MUNICIPALITY_CODE_COLUMN: str = "시정촌코드"
PREFECTURE_COLUMN: str = "부현"
MUNICIPALITY_KO_COLUMN: str = "시정촌(한글)"
MUNICIPALITY_JA_COLUMN: str = "시정촌(日)"


# 통계 XLSX exposure 컬럼
POPULATION_COLUMN: str = "population"
HOUSEHOLDS_COLUMN: str = "households_general"

# 7. USGS 컬럼 정의
USGS_LS_PRIOR_COLUMN: str = "LS_prior(평균)"
USGS_LQ_PRIOR_COLUMN: str = "LQ_prior(평균)"
USGS_PGV_COLUMN: str = "PGV"

# 8. dtype 정의
# 첫 구현에서는 확률/우도 계산의 수치 안정성 위해 float64 사용 

DTYPE: torch.dtype = torch.float64

# event_idx, muni_code와 같은 index/식별자는 소수점 필요하지 않기에 정수형 사용
INDEX_DTYPE: torch.dtype = torch.long

# 9. EPS 정의
"""
EPS는 교수님 피드백에서 추가된 수치 안정성 규칙이다.

B의 prior.py에서는 다음 계산을 한다.

    logit(pi) = log(pi / (1 - pi))

그런데 실제 USGS prior에는 0이 존재할 수 있다.

pi = 0이면:

    logit(0)
    = log(0 / 1)
    = -infinity

가 되어 학습이 깨질 수 있다.

pi = 1 역시 +infinity 문제가 발생한다.


그래서 prior.py에서:

    torch.clamp(
        pi,
        min=EPS,
        max=1-EPS
    )

를 먼저 적용한다.


clamp란?
--------

값을 지정된 범위 밖으로 나가지 못하게 잘라주는 함수이다.

EPS = 0.000001일 때
    0
        -> 0.000001
    0.2
        -> 0.2
    0.7
        -> 0.7
    1
        -> 0.999999

중요:
-----
schema.py에서는 EPS라는 "공통 규칙"만 정의한다.

실제로 clamp를 실행하는 코드는 B의 prior.py에 들어간다.
"""
EPS: float = 1e-6

# 10. loader.py가 만들어야 하는 공통 배치 구조
@dataclass 
class PilotABatch:
    """
    loader.py가 최종적으로 만들어서 A와 B가 함께 사용하는 한 batch의 데이터 구조
    -> 여러 tensor를 한 상자에 넣은 것

    -------------------
    1. y
    -------------------
    shape [B,6] 실제 피해 건수 
    채널 순서 : 사망 중상 경상 전파 반파 일부 파손
    실제 예 : 아쓰마초 [36, 0, 61, 224, 318, 1097]

    -------------------
    2. E
    -------------------
    shape [B,6] 각 피해 채널의 exposure
    실제 예 : 아쓰마초 population = 4838, households_general = 2121
    -> E=[4838,4838,4838,2121,2121,2121]

    -------------------
    3. PGV
    -------------------
    shape [B] USGS Shakemap 기반 시정촌별 PGV
    regression.py의 log(PGV) 계산에 사용 

    -------------------
    4. pi_ls / pi_lq
    -------------------
    shape [B] 산사태/액상화 USGS prior
    실제 원본 컬럼 LS_prior(평균) / LQ_prior(평균) 사용
    -> B의 prior.py에서 사용

    -------------------
    6. event_idx
    -------------------
    shape [B] 각 행이 어느 지진 이벤트인지 나타내는 idx
    dtype torch.long
    범위 0~7

    -------------------
    7. obs_mask
    -------------------
    shape [B,6] 해당 피해 채널 값이 실제 관측된 값인지 표시
    -> True : 실제 피해 값 존재, False : 원본 데이터가 '-'등 결측
    dtype torch.bool

    예:
        아쓰마초

        [True, True, True, True, True, True]

        고리야마시
        raw y =
        [0, 1, 12, 17, 987, "-"]

        loader y =
        [0, 1, 12, 17, 987, 0]

        obs_mask =
        [True, True, True, True, True, False]


    주의
        고리야마시 마지막 y=0은
        "피해가 0건"이라는 의미가 아니다.

        Tensor를 만들기 위한 placeholder이고,
        실제 결측 여부는 obs_mask=False가 표현한다.

        이 mask를 실제 likelihood 계산에 적용하는 곳은
        A의 likelihood.py이다.

    -----------------------------------
    8. event_idx + municipality_code
    -----------------------------------
    이 두 값을 합치면 원래 시정촌x지진 이벤트 다시 식별 ㅇ
    예:
    event_idx = 5, municipality_code = 1581 -> 2018 훗카이도 / 아쓰마초
    """

    # 실제 모델 계산에 사용하는 tensor
    y: Tensor 
    E: Tensor 
    pgv: Tensor
    pi_ls: Tensor 
    pi_lq: Tensor 
    event_idx: Tensor 
    obs_mask: Tensor 

    # 결과를 다시 원본 시정촌과 연결하기 위한 식별자
    municipality_code: Tensor 

    @property
    def batch_size(self)->int: 
        """
        현재 batch에 포함된 행 개수 반환
        입력 : 별도 입력 x
        출력 : int 
        실제 예 : 전체 383행 한 번에 넣으면 ? 
        -> self.y.shape = [383,6]
        -> self.batch_size = 383

        나중에 미니 배치 64 사용하면 ? 
        -> self.y.shape = [64,6]
        -> self.batch_size = 64
        """

        return self.y.shape[0]

    def validation(self)->None: 
        """
        PilotABatch가 모델에 들어갈 수 있는 정상적인 데이터인지 검사
        이 함수는 데이터 수정하지 않고, 단순히
        batch.validate() 호출 시 
        정상 데이터 -> 아무일없이 종료
        잘못된 데이터 -> ValueError 또는 TypeError 발생 

        입력 : 별도 입력 없음 
        출력 : 정상일 경우 -> None 
        """

        # 현재 batch 행 개수
        B = self.batch_size 
        if B <= 0:
            raise ValueError(
                "batch에는 최소 1개 이상의 행이 있어야 합니다."
            )

        # 1. [B,6] Tensor shape 검사
        expected_matrix_shape = (B, NUM_CHANNELS)

        matrix_tensors = {
            "y": self.y, "E": self.E, "obs_mask": self.obs_mask,
        }

        for name, tensor in matrix_tensors.items():
            if tuple(tensor.shape) != expected_matrix_shape:
                raise ValueError(
                    f"{name} shape 오류: "
                    f"expected={expected_matrix_shape}, "
                    f"actual={tuple(tensor.shape)}"
                )

        # 2. [B] Tensor shape 검사 
        expected_vector_shape = (B,)

        vector_tensors={
            "pgv":self.pgv,
            "pi_ls":self.pi_ls,
            "pi_lq":self.pi_lq,
            "event_idx": self.event_idx,
            "municipality_code":self.municipality_code,
        }

        for name, tensor in vector_tensors.items():
            if tuple(tensor.shape) != expected_vector_shape:

                raise ValueError(
                    f"{name} shape 오류: "
                    f"expected={expected_vector_shape}, "
                    f"actual={tuple(tensor.shape)}"
                )

        # 3. float tensor dtype 
        float_tensors={
            "y":self.y, 
            "E":self.E,
            "pgv":self.pgv,
            "pi_ls":self.pi_ls,
            "pi_lq":self.pi_lq,
        }

        for name, tensor in float_tensors.items():
            if tensor.dtype != DTYPE:
                raise TypeError(
                    f"{name} dtype 오류: "
                    f"expected={DTYPE}, "
                    f"actual={tensor.dtype}"
                )


        # 4. obs_mask dtype 검사 
        if self.obs_mask.dtype != torch.bool:

            raise TypeError(
                "obs_mask는 torch.bool dtype이어야 합니다."
            )

        # 5. index tensor dtype 검사 
        index_tensors = {
            "event_idx": self.event_idx,
            "municipality_code": self.municipality_code,
        }

        for name, tensor in index_tensors.items():
            if tensor.dtype != INDEX_DTYPE:
                raise TypeError(
                    f"{name} dtype 오류: "
                    f"expected={INDEX_DTYPE}, "
                    f"actual={tensor.dtype}"
                )

        # 6. NaN / Inf 검사
        """
        NaN : 숫자가 아님
        Inf: 무한대 또는 -무한
        이런 값 하나만 모델에 들어가도 전체 loss가 NaN 될 수 있어서 모델 시작 전 차단
        """

        for name, tensor in float_tensors.items():
            if not torch.isfinite(tensor).all():
                raise ValueError(
                    f"{name}에 NaN 또는 Inf가 존재합니다."
                )

        # 7. y 범위 검사 
        # 피해 건수는 음수가 될 수 없음

        if (self.y < 0).any():

            raise ValueError(
                "y에는 음수 피해 건수가 존재할 수 없습니다."
            )

        # 실제 관측된 피해 건수는 정수여야 한다.
        # y dtype 자체는 계산 편의를 위해 float64이지만 
        # 36.0, 61.0처럼 정수 형태의 값이어야 한다.
        observed_y = self.y[self.obs_mask]

        if not torch.allclose(
            observed_y,
            observed_y.round(),
        ):

            raise ValueError(
                "관측된 y는 피해 건수이므로 정수 값이어야 합니다."
            )

        # 결측 채널은 loader.py에서 placeholder로 반드시 0 넣기로 
        # 예 : raw = '-' -> y = 0, obs_mask = False 
        missing_y = self.y[~self.obs_mask] # 결측치 자리만 True로 변경됨 

        if missing_y.numel() > 0: # 데이터 총 개수 세는 함수 

            if (missing_y != 0).any(): # 비어있어야 할 자리에 0이 아닌 다른 값이 들어왔는지 

                raise ValueError(
                    "결측 채널의 y placeholder는 0이어야 합니다."
                )

        # 8. Exposure 검사 
        """
        E는 population 또는 households_general 이므로 반드시 0보다 커야함
        이후 regression.py에서 mu = E * lambda 계산에 사용됨
        """
        if (self.E <= 0).any():

            raise ValueError(
                "E(exposure)는 모든 채널에서 0보다 커야 합니다."
            )

        # 9. PGV 검사
        """
        regression.py에선 PGV에 로그 취함 -> PGV=0이면 log(0) = -infinity 문제됨
        """  


        if (self.pgv <= 0).any():

            raise ValueError(
                "PGV는 반드시 0보다 커야 합니다."
            )

        # 10. USGS prior 범위 검사
        """
        USGS prior는 확률이므로 0<=pi<=1 범위어야함
        여기선 0,1 자체를 오류로 처리 x 
        다만 B의 prior.py에서 logit 계산하기 직전 clamp 적용
        """
        if (
            (self.pi_ls < 0)
            | (self.pi_ls > 1)
        ).any():

            raise ValueError(
                "pi_ls는 [0, 1] 범위여야 합니다."
            )


        if (
            (self.pi_lq < 0)
            | (self.pi_lq > 1)
        ).any():

            raise ValueError(
                "pi_lq는 [0, 1] 범위여야 합니다."
            )


        # 11. event_idx 범위 검사
        # 이벤트가 총 8개이므로 0-7 사이어야함
        invalid_event = (
            (self.event_idx < 0)
            | (self.event_idx >= NUM_EVENTS)
        )

        if invalid_event.any():

            raise ValueError(
                f"event_idx는 0 ~ {NUM_EVENTS - 1} "
                "범위여야 합니다."
            )

        # 12. 시정촌 코드 검사
        # 실제 시정촌코드는 양의 정수이므로
        # 0 이하 값이 들어오면 join/전처리 오류로 간주

        if (self.municipality_code <= 0).any():

            raise ValueError(
                "municipality_code는 양의 정수여야 합니다."
            )


 

