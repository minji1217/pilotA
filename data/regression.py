"""
pilot A - model/regression.py 

loader.py가 만든 PilotABatch에서 E, PGV, event_idx를 받아 잠재상태 4개
(00, 10, 01, 11) 각각에 대해 피해 6채널의 기대피해 건수 mu 계산

pilotABatch 실제 데이터 형태 
필드	    실제 shape	    dtype	        의미
y	        [382, 6]	torch.float64	피해 6채널 관측값
E   	    [382, 6]	torch.float64	피해 6채널 Exposure
pgv 	    [382]	    torch.float64	각 시정촌×이벤트 행의 PGV
pi_ls	    [382]	    torch.float64	LS prior 평균
pi_lq	    [382]	    torch.float64	LQ prior 평균
event_idx	[382]   	torch.int64	    8개 지진 이벤트 중 어떤 이벤트인지
obs_mask	[382, 6]	torch.bool	    각 피해 채널이 실제 관측됐는지
municipality_code	길이 382	tuple[str, ...]	"01581" 같은 5자리 시정촌 ID



설계식 : 
    log(lambda_ice) = alpha_c + alpha_e + beta_c * log(PGV_ie)
                      + gamma_c^LS * LS + gamma_c^LQ * LQ
    lambda_ice = exp(log(lambda_ice))
    mu_ice = E_ice * lambda_ice

입력 shape:
    E [B,6]
    pgv [B]
    event_idx [B]

출력 shape:
    log_lambda [B,4,6]
    lambda_rate [B,4,6]
    mu [B,4,6]

실제 아쓰마초 한 행 예:
    E = [4838, 4838, 4838, 2121, 2121, 2121]
    pgv = 44.64
    event_idx = 5

이 한 행이 00/10/01/11 네 상태로 확장되므로 최종 mu의 한 행 shape은 [4, 6]이다.
실제 mu 숫자는 alpha, beta, gamma의 학습값에 따라 달라지므로 코드에 고정하지 않는다.  
"""

from __future__ import annotations

from dataclasses import dataclass

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch import Tensor

from data.schema import (
    DTYPE,
    EPS,
    LATENT_STATES,
    NUM_CHANNELS,
    NUM_EVENTS,
    NUM_STATES,
    PilotABatch,
)

@dataclass 
class RegressionOutput:
    """
    regression.py의 계산 결과를 한 객체로 묶는다.
    입력 : DamageRegression.forward() 내부 계산 결과 
    출력 필드 : 
    - log_lambda [B,4,6] : 피해율 lambda에 log취한값
    - lambda_rate [B,4,6] : 피해율 lambda 
    - mu [B,4,6] : negatvie binomial에 넘길 기대피해 건수

    실제 아쓰마초 한 행은 각 필드에서 [4,6] 부분을 가진다. 
    4는 00 10 01 11, 6은 사망 중상 경상 전파 반파 일부파손이다.
    """

    log_lambda : Tensor
    lambda_rate: Tensor 
    mu: Tensor 

class DamageRegression(nn.Module):
    """
    PGV, E, 이벤트 효과, LS/LQ 상태를 이용해 mu 계산하는 회귀

    학습 파라미터:
    - alpha_channel [6] : 피해 채널별 기본 수준
    - alpha_event [8] : 지진 이벤트별 공통 효과
    - beta_pgv [6] : 채널별 log(PGV) 효과 
    - raw_gamma_ls [6] : softplus 전 LS 효과
    - raw_gamma lq [6] : softplus 전 LQ 효과

    gamma는 softplus를 거쳐 항상 0이상이 된다.
    - alpha_event_free [7]은 기준 이벤트 제외한 alpha_e의 자유 파라미터
    - _gamma_ls_unconstrained, _gamma_lq_unconstrained는 gamma>=0 제약 위한 내부 표현
    """

    def __init__(
            self, *, reference_event_idx: int = 0, gamma_init: float = 0.1, 
    )-> None:
        """
        회귀모형 파라미터 생성
        reference_event_idx : alpha_e=0으로 고정할 기준 이벤트 idx.
        gamma_init: softplus 적용 후 실제 gamma 초기값. (0.1)

        생성 직후:
            alpha_channel은 임시 0이며 train 시작 전에 initialize_from_batch(batch)로 실제 관측 피해율에서 초기화한다.
            alpha_event 전체 효과는 모두 0이다.
            beta_pgv는 모두 0이다.
            gamma_ls, gamma_lq는 모두 0.1이다.
        """
        super().__init__()

        if not 0<= reference_event_idx < NUM_EVENTS:
            raise ValueError(f"reference_event_idx는 0~{NUM_EVENTS - 1} 범위여야 합니다.")
        if gamma_init <= 0:
            raise ValueError("gamma_init은 0보다 커야 합니다.")

        self.reference_event_idx = int(reference_event_idx)
        self.gamma_init = float(gamma_init)

        # alpha_c [6] : 채널별 기본 log 피해율. 실제 batch로 다시 초기화할 것이기에 우선 0으로 파라미터만 생성
        self.alpha_channel = nn.Parameter(torch.zeros(NUM_CHANNELS, dtype=DTYPE))

        # alpha_e는 개념적으로 8개지만 기준 이벤트 하나는 0이므로 optimizer가 움직일 자유값은 7개
        self.alpha_event_free = nn.Parameter(torch.zeros(NUM_EVENTS -1, dtype=DTYPE))

        # beta_c [6] : PGV가 피해 6채널 각각에 미치는 효과 
        self.beta_pgv = nn.Parameter(torch.zeros(NUM_CHANNELS, dtype=DTYPE))

        # 실제 gamma = 0.1이 softplus 이후 정확히 나오도록 내부 unconstrained 초기값 계산
        gamma_unconstrained_init = _inverse_softplus(self.gamma_init)
        self._gamma_ls_unconstrained = nn.Parameter(
            torch.full((NUM_CHANNELS,), gamma_unconstrained_init, dtype=DTYPE)
        )
        self._gamma_lq_unconstrained = nn.Parameter(
            torch.full((NUM_CHANNELS,), gamma_unconstrained_init, dtype=DTYPE)
        )

    @property 
    def alpha_event(self) -> Tensor:
        """
        기준 이벤트가 0으로 고정된 전체 alpha_e [8] 생성 
        
        reference_event_idx=0이면:
            [0, free_1, free_2, ..., free_7]
        
        기준 이벤트의 0은 "효과없음"이 아니라 다른 이벤트 효과 비교위한 기준점
        """
        zero = self.alpha_event_free.new_zeros(1)

        # 3을 예로 든다면 
        return torch.cat(
            [   
                # [0.41, -0.18, 0.63]
                self.alpha_event_free[:self.reference_event_idx],
                zero,
                # [0.09, -0.35, 0.22, 0.77]
                self.alpha_event_free[self.reference_event_idx:],
            ],dim=0,
        )
            # [0.41, -0.18, 0.63, 0.0, 0.09, -0.35, 0.22, 0.77]
            #                     ↑ 3번 자리에 0
        

    @property
    def gamma_ls(self)-> Tensor:
        """
        gamma_c^LS [6]반환
        내부값에 softplus 적용하므로 항상 0이상이며 초기값은 모두 0.1
        """
        return F.softplus(self._gamma_ls_unconstrained)

    @property
    def gamma_lq(self) -> Tensor:
        """
        PDF의 gamma_c^LQ [6]을 반환한다.

        내부값에 softplus를 적용하므로 항상 0 이상이며 초기값은 모두 0.1이다.
        """
        return F.softplus(self._gamma_lq_unconstrained)

    @torch.no_grad()
    def initialize_from_batch(self, batch: PilotABatch)-> Tensor:
        """
        실제 입력 :
        - batch.y [B,6]
        - batch.E [B,6]
        - batch.obs_mask [B,6]

        적용:
        1. alpha_c = log(sum(y_c)/sum(E_c))
        2. alpha_e = 모두 0, 기준 이벤트는 구조적으로 계속 0
        3. beta_c = 0
        4. gamma_c^LS = 0.1
        5. gamma_c^LQ = 0.1

        결측 피해 채널은 obs_mask=False이므로 alpha_c 초기화의 피해합/Exposure합에서 모두 제외됨
        """

        batch.validate()

        # True=1, False=0으로 바꿔 관측된 채널만 합계에 포함
        observed = batch.obs_mask.to(dtype = DTYPE)

        # 채널별 실제 관측 피해합과 같은 관측 위치의 exposure 합을 계산 
        total_y = (batch.y * observed).sum(dim=0)
        total_E = (batch.E * observed).sum(dim=0)

        if (total_E <= 0).any():
            raise ValueError("alpha_c 초기화용 Exposure 합은 모든 채널에서 0보다 커야 합니다.")

        # 피해합이 0인 채널이 있으면 log(0)을 피하기 위해 EPS를 최소값으로 둠     
        # 사망 : 모든 시정촌이 0이면 0됨 
        
        empirical_rate = torch.clamp(total_y / total_E, min=EPS)
        alpha_init = torch.log(empirical_rate)

        # parameter 객체는 유지하고 값만 권장 초기값으로 덮어씀
        self.alpha_channel.copy_(alpha_init)
        self.alpha_event_free.zero_()
        self.beta_pgv.zero_()

        return alpha_init.clone()

    def forward(self, batch: PilotABatch) -> RegressionOutput:
        """
        batch의 모든 행을 4개 잠재상태로 확장해 6채널 mu 계산

        실제 아쓰마초 입력 예:
            E = [4838,4838,4838,2121,2121,2121]
            pgv = 44.64
            event_idx = 5

        처리:
            pgv 44.64 하나에 채널별 beta_c [6]이 각각 곱해진다.
            event_idx=5이면 alpha_event[5]를 선택한다.
            00/10/01/11 네 상태 각각에서 6채널 log_lambda를 계산한다.
            lambda = exp(log_lambda)
            mu = E * lambda

        출력:
            아쓰마초 한 행 -> mu [4,6]
            전체 B행 -> mu [B,4,6]
        """

        batch.validate()
        B = batch.batch_size 

        # 실제 PGV는 행마다 하나라 [B]이고, [B,1,1]로 바꾸어 상태 4개와 채널 6개에 broadcast
        log_pgv = torch.log(batch.pgv).view(B,1,1)

        # 기준 이벤트 0을 포함한 전체 alpha_e [8]에서 각 행의 event_idx에 해당하는 효과 선택
        event_effect = self.alpha_event[batch.event_idx].view(B,1,1)

        # 채널별 파라미터 [6]을 [1,1,6]으로 바꾸어 모든 행과 상태에 적용
        channel_intercept = self.alpha_channel.view(1,1,NUM_CHANNELS)
        pgv_effect = self.beta_pgv.view(1,1, NUM_CHANNELS)
        gamma_ls = self.gamma_ls.view(1,1,NUM_CHANNELS)
        gamma_lq = self.gamma_lq.view(1,1,NUM_CHANNELS)

        # schema.py의 고정 잠재상태 순서 00 10 01 11을 Tensor [4,2]로 만든다
        states = torch.tensor(
            LATENT_STATES, 
            dtype = DTYPE, 
            device = batch.E.device, 
        )

        ls_state = states[:, 0].view(1, NUM_STATES, 1)
        lq_state = states[:, 1].view(1, NUM_STATES, 1)

        # 로그 선형 회귀식을 벡터화한 결과이며 shape은 [B,4,6]
        log_lambda = (
            channel_intercept + event_effect +
            pgv_effect * log_pgv 
            +gamma_ls * ls_state + gamma_lq * lq_state
        )

        # log 피해율을 원래 양수 scale로 되돌림 
        lambda_rate = torch.exp(log_lambda)

        # E [B,6]에 상태 축을 추가한 [B,1,6]과 lambda [B,4,6]을 곱해 기대피해 mu를 만든다.
        mu = batch.E.unsqueeze(1) * lambda_rate

        if not torch.isfinite(log_lambda).all():
            raise ValueError("log_lambda에 NaN 또는 Inf가 발생했습니다.")
        if not torch.isfinite(lambda_rate).all():
            raise ValueError("lambda_rate에 NaN 또는 Inf가 발생했습니다.")
        if not torch.isfinite(mu).all():
            raise ValueError("mu에 NaN 또는 Inf가 발생했습니다.")
        if (mu <= 0).any():
            raise ValueError("mu는 모든 행/상태/채널에서 0보다 커야 합니다.")

        return RegressionOutput(
            log_lambda=log_lambda,
            lambda_rate=lambda_rate,
            mu=mu,
        )



def _inverse_softplus(value: float) -> float:
    """
    원하는 실제 gamma 초기값을 softplus 이전 내부값으로 변환
    gamma=0.1이면 내부값은 약 -2.252이고 softplus 거치면 다시 0.1이 됨
    이 내부값은 별도 파라미터가 아닌 gamma>=0 제약 위한 구현 표현
    """
    if value <= 0:
        raise ValueError("inverse softplus 입력은 0보다 커야 합니다.")
    return float(
        torch.log(
            torch.expm1(
                torch.tensor(value, dtype = DTYPE)
            )
        ).item()
    )