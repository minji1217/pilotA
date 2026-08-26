# Y ~ NegBin(mu, phi)인데 pytorch는 total_count, probs를 받음
# 평균 = mu, 분산 = mu + (mu^2/phi) 
# phi -> total_count
# mu, phi -> probs = mu / (mu + phi)
# -> pytorch 분포의 평균이 mean = mu가 됨 

"""
Pilot A - model/likelihood.py

regression.py가 계산한 mu [B,4,6]와 실제 피해 y[B,6]을 NB로 잠재상태 4개(00 10 01 11)의 
log-likelihood log_L [B,4] 계산

설계:
    Y_ice ~ NegBin(mu_ice, phi_c)
    Var(Y_ice) = mu_ice + mu_ice^2 / phi_c
    L_s = product_c P_NB(y_c | mu_{s,c}, phi_c)

수치 안정성 위해 실제 구현은 log합 
입력:
    batch.y        [B,6]
    batch.obs_mask [B,6]
    mu             [B,4,6]

출력:
    log_p_nb        [B,4,6]  # mask 적용 전 채널별 log-PMF
    masked_log_p_nb [B,4,6]  # 결측 채널을 0으로 만든 log-PMF
    log_L           [B,4]    # 채널 log-PMF 합
"""
from __future__ import annotations

from dataclasses import dataclass

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch import Tensor

from data.schema import DTYPE, NUM_CHANNELS, NUM_STATES, PilotABatch

@dataclass 
class LikelihoodOutput:
    """
    likelihood.py의 결과
    log_p_nb : [B,4,6] 각 시정촌x 이벤트 행에서 4개 잠재상태 x 6채널 각각의 NB log-PMF
    masked_log_p_nb:
        [B,4,6]
        obs_mask=False인 결측 채널을 0으로 바꾼 값.
        log-space에서 0은 곱셈 원래 scale의 1에 해당하므로 합산 결과에 영향을 주지 않는다.

    log_L:
        [B,4]
        채널 6개의 masked log-PMF를 합한 4개 잠재상태별 log-likelihood.  
    """
    log_p_nb: Tensor 
    masked_log_p_nb: Tensor 
    log_L : Tensor 

class DamageLikelihood(nn.Module):
    """
    mu와 실제 y를 NB로 비교해 log_L 계산 
    pdf의 학습 대상:
    - phi_c [6] : 피해 채널별 과분산 모수, phi_c > 0

    내부 구현:
    - _phi_unconstrained [6]은 phi>0 제약을 softplus로 구현하기 위한 내부 표현 
    - 모델 관점의 실제 학습 파라미터는 phi_c [6] 하나의 셋
    """


    def __init__(self, *, phi_init: float = 5.0) -> None:
        """
        채널별 phi 파라미터를 만든다.

        phi_init:
            PDF 권장 초기값 5.0.
            실제 phi가 5.0이 되도록 softplus 이전 내부값을 역변환해 Parameter로 저장한다.
        """
        super().__init__()

        if phi_init <= 0:
            raise ValueError("phi_init은 0보다 커야 합니다.")

        self.phi_init = float(phi_init)

        phi_unconstrained_init = _inverse_softplus(self.phi_init)
        self._phi_unconstrained = nn.Parameter(
            torch.full(
                (NUM_CHANNELS,),
                phi_unconstrained_init,
                dtype=DTYPE,
            )
        )

        # PyTorch NegativeBinomial의 parameterization이 설계식과 맞는지 첫 forward에서 한 번만 검사한다.
        self._nb_parameterization_checked = False

    @property 
    def phi(self)->Tensor:
        """
        PDF의 실제 phi_c [6]반환
        softplus 적용하므로 모든 채널에서 항상 0보다 큼 
        초기값은 [5,5,5,5,5,5]
        """

        return F.softplus(self._phi_unconstrained)

    def forward(self, batch: PilotABatch, mu:Tensor) -> LikelihoodOutput:
        """
        실제 피해 y와 regression.py의 mu를 비교해 상태별 log_L 계산
        입력 예:
            batch.y [B,6]
            batch.obs_mask [B,6]
            mu [B,4,6]

        처리:
        1. phi [6] -> [1,1,6]
        2. y [B,6] -> [B,1,6]
        3. probs = mu / (mu + phi)
        4. NegativeBinomial(...).log_prob(y) -> [B,4,6]
        5. obs_mask=False인 채널의 log-PMF를 0으로 변경
        6. 채널 축을 sum하여 log_L [B,4] 생성

        반환:
            LikelihoodOutput(log_p_nb, masked_log_p_nb, log_L)
        """

        batch.validate()
        B=batch.batch_size

        expected_mu_shape = (B, NUM_STATES, NUM_CHANNELS)
        if tuple(mu.shape) != expected_mu_shape:
            raise ValueError(
                f"mu shape 오류: expected={expected_mu_shape}, actual={tuple(mu.shape)}"
            )
        if mu.dtype != DTYPE:
            raise TypeError(f"mu dtype 오류: expected={DTYPE}, actual={mu.dtype}")
        if not torch.isfinite(mu).all():
            raise ValueError("mu에 NaN 또는 Inf가 존재합니다.")
        if (mu <= 0).any():
            raise ValueError("mu는 모든 행/상태/채널에서 0보다 커야 합니다.")

        # phi는 채널마다 하나이므로 [6] -> [1,1,6]으로 만들어 B행과 4상태에 broadcast한다.
        phi_broadcast = self.phi.view(1, 1, NUM_CHANNELS)

        # PyTorch NegativeBinomial에서 mean=mu가 되도록 probs=mu/(mu+phi)를 사용한다.
        probs = mu / (mu + phi_broadcast)

        dist = torch.distributions.NegativeBinomial(
            total_count=phi_broadcast,
            probs=probs,
        )

        # 첫 forward에서만 mean/var이 설계식과 같은지 확인 
        if not self._nb_parameterization_checked:
            self._check_negative_binomial_parameterization(
                dist=dist,
                mu=mu,
                phi_broadcast=phi_broadcast,
            )
            self._nb_parameterization_checked = True

        # y는 상태에 따라 바뀌지 않는 실제 관측값이므로 [B,6] -> [B,1,6]으로 상태 축만 추가
        y_broadcast = batch.y.unsqueeze(1)

        # 각 행x상태x채널의 log-PMF. 확률값으로 되돌리지 않고 계속 log-space 
        log_p_nb = dist.log_prob(y_broadcast)
        # loader가 만든 mask를 여기서 적용한다.
        # 결측 채널은 log-space에서 0으로 만들어 이후 sum에 아무 영향도 주지 않게 한다.
        mask_broadcast = batch.obs_mask.unsqueeze(1)
        masked_log_p_nb = torch.where(
            mask_broadcast,
            log_p_nb,
            torch.zeros_like(log_p_nb),
        )
        # 원래 수학식의 채널별 확률 곱을 log-space의 합으로 계산한다.
        # [B,4,6] -> 채널축 sum -> [B,4]
        log_L = masked_log_p_nb.sum(dim=-1)

        if tuple(log_p_nb.shape) != expected_mu_shape:
            raise RuntimeError(
                f"log_p_nb shape 오류: expected={expected_mu_shape}, actual={tuple(log_p_nb.shape)}"
            )
        if tuple(masked_log_p_nb.shape) != expected_mu_shape:
            raise RuntimeError(
                "masked_log_p_nb shape 오류: "
                f"expected={expected_mu_shape}, actual={tuple(masked_log_p_nb.shape)}"
            )
        if tuple(log_L.shape) != (B, NUM_STATES):
            raise RuntimeError(
                f"log_L shape 오류: expected={(B, NUM_STATES)}, actual={tuple(log_L.shape)}"
            )
        if not torch.isfinite(log_L).all():
            raise ValueError("log_L에 NaN 또는 Inf가 발생했습니다.")

        return LikelihoodOutput(
            log_p_nb=log_p_nb,
            masked_log_p_nb=masked_log_p_nb,
            log_L=log_L,
        )





    @torch.no_grad()
    def _check_negative_binomial_parameterization(
        self,
        *,
        dist:torch.distributions.NegativeBinomial,
        mu:Tensor,
        phi_broadcast:Tensor,
    )->None:
        """
        pytorch NB 설정이 설계식과 일치하는지 한 번만 검증
        확인: dist.mean == mu
        dist.variance == mu+mu^2/phi

        이 검사는 학습 로직이 아니라 구현 실수를 조기에 잡기 위한 체크포인트임
        """
        expected_variance =  mu + (mu.square() / phi_broadcast)
    

        if not torch.allclose(dist.mean, mu, rtol=1e-7, atol=1e-10):
            raise RuntimeError(
                "NegativeBinomial parameterization 오류: dist.mean이 mu와 일치하지 않습니다."
            )

        if not torch.allclose(
            dist.variance,
            expected_variance,
            rtol=1e-7,
            atol=1e-10,
        ):
            raise RuntimeError(
                "NegativeBinomial parameterization 오류: "
                "dist.variance가 mu + mu^2/phi와 일치하지 않습니다."
            )
        

def _inverse_softplus(value: float) -> float:
    """
    원하는 실제 phi 초기값을 softplus 이전 내부값으로 변환한다.

    예:
        phi=5.0
        -> 내부값 약 4.993
        -> softplus(4.993...) = 5.0

    내부값은 별도 모델 파라미터가 아니라 phi>0 제약을 구현하기 위한 표현이다.
    """
    if value <= 0:
        raise ValueError("inverse softplus 입력은 0보다 커야 합니다.")

    return float(
        torch.log(
            torch.expm1(
                torch.tensor(value, dtype=DTYPE)
            )
        ).item()
    )
