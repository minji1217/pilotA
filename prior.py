import math

import torch
import torch.nn as nn
from torch import Tensor
import torch.nn.functional as F
from schema import EPS,LATENT_STATES,DTYPE

# 내가 이 파일에서 해야할것
# 1.w를 구하는것 (w00,w10,w01,w11)
# 2.marginalize 주변화는 다른 파일에서 할거여서 지금은 w만들기만
# 3.a*logit(pi)+b

# 민지님께서 만들어 주신 클래스를 통해서 데이터를 USGS 산사태/액상화 가져옴


def _inverse_sigmoid(p: float) -> float:
    """sigmoid(x)=p가 되는 x. 재파라미터화 초기값 계산용."""
    return math.log(p / (1.0 - p))


class Prior(nn.Module):
    """USGS prior를 z = a*logit(pi) + b 로 보정한 뒤 4상태 prior를 만든다.

    mode
    ----
    "free"    : a, b를 제약 없이 학습한다. (기존 동작)
                실제로 b_LS가 10.2까지 커져 prior를 망가뜨리는 것이 확인됐다.

    "fixed"   : a=1, b=0으로 고정한다. sigmoid(logit(pi))=pi 이므로
                USGS prior를 손대지 않고 그대로 쓴다. 학습 파라미터가 아니다.

    "bounded" : a in [0.5, 2], b in [b_min, b_max] 범위 안에서만 학습한다.
                clamp는 경계에서 gradient가 0이 되어 학습이 멈추므로
                sigmoid 재파라미터화를 쓴다. 초기값은 정확히 a=1, b=0이다.
                b 범위는 기본이 ±b_bound(=[-2,2])이고,
                후속실험 2처럼 비대칭이 필요하면 b_min/b_max로 준다(=[-2,4]).
    """

    MODES = ("free", "fixed", "bounded")

    A_MIN, A_MAX = 0.5, 2.0
    B_MIN, B_MAX = -2.0, 2.0

    def __init__(self, *args, mode: str = "free", b_bound: float = 2.0,
                 b_min=None, b_max=None, mtn_prior: bool = False, **kwargs):
        super().__init__(*args, **kwargs)

        # 후속실험 3(LOEO): 켜면 z_LS에 kappa * z_mtn(표준화 산지 비율)을 더한다.
        # 기본값 False에서는 파라미터도 만들지 않으므로 기존 결과가 그대로 재현된다.
        self.mtn_prior = bool(mtn_prior)

        if mode not in self.MODES:
            raise ValueError(f"mode는 {self.MODES} 중 하나여야 합니다: {mode}")
        self.mode = mode

        # 실험에서 b가 상한에 계속 붙어 나와 범위를 조절할 수 있게 인스턴스 값으로 둔다.
        #
        # 후속실험 2의 b 범위 [-2, 4]는 비대칭이라 b_bound 하나로는 표현할 수 없다.
        # b_min/b_max를 주면 그쪽을 쓰고, 안 주면 기존처럼 ±b_bound가 된다.
        if b_min is None and b_max is None:
            if b_bound <= 0:
                raise ValueError(f"b_bound는 0보다 커야 합니다: {b_bound}")
            b_min, b_max = -float(b_bound), float(b_bound)
        elif b_min is None or b_max is None:
            raise ValueError("b_min과 b_max는 함께 지정해야 합니다.")
        else:
            b_min, b_max = float(b_min), float(b_max)

        # 초기값을 b=0으로 잡으므로 0이 범위 안쪽에 있어야 한다.
        # 경계에 걸리면 _inverse_sigmoid가 발산한다.
        if not b_min < 0.0 < b_max:
            raise ValueError(
                f"b 범위는 0을 안쪽에 포함해야 합니다(초기값 b=0): [{b_min}, {b_max}]"
            )
        self.B_MIN, self.B_MAX = b_min, b_max

        if mode == "free":
            self.a=nn.Parameter(torch.ones(2,dtype=DTYPE))
            self.b=nn.Parameter(torch.zeros(2,dtype=DTYPE))

        elif mode == "fixed":
            # buffer로 두면 optimizer가 잡아가지 않으므로 학습되지 않는다.
            self.register_buffer("a", torch.ones(2, dtype=DTYPE))
            self.register_buffer("b", torch.zeros(2, dtype=DTYPE))

        else:  # bounded
            # a=1, b=0에서 시작하도록 raw 초기값을 역산한다.
            a_init = _inverse_sigmoid((1.0 - self.A_MIN) / (self.A_MAX - self.A_MIN))
            b_init = _inverse_sigmoid((0.0 - self.B_MIN) / (self.B_MAX - self.B_MIN))
            self._a_raw = nn.Parameter(torch.full((2,), a_init, dtype=DTYPE))
            self._b_raw = nn.Parameter(torch.full((2,), b_init, dtype=DTYPE))

        if self.mtn_prior:
            # 산지 계수. 스칼라 하나, 초기값 0, 범위 제약 없음, LS에만 들어간다.
            self.kappa = nn.Parameter(torch.zeros(1, dtype=DTYPE))

    @property
    def a_value(self) -> Tensor:
        """실제 식에 들어가는 a [2]. LS=0, LQ=1."""
        if self.mode == "bounded":
            return self.A_MIN + (self.A_MAX - self.A_MIN) * torch.sigmoid(self._a_raw)
        return self.a

    @property
    def b_value(self) -> Tensor:
        """실제 식에 들어가는 b [2]. LS=0, LQ=1."""
        if self.mode == "bounded":
            return self.B_MIN + (self.B_MAX - self.B_MIN) * torch.sigmoid(self._b_raw)
        return self.b

    def z(self, pi_ls, pi_lq, z_mtn=None):
        """z_LS, z_LQ [B]. prior 확률 q = sigmoid(z)를 BCE에 쓰려고 분리해 두었다."""
        x_ls=torch.logit(pi_ls,eps=EPS)
        x_lq=torch.logit(pi_lq,eps=EPS)

        a, b = self.a_value, self.b_value

        z_ls=a[0]*x_ls+b[0]
        z_lq=a[1]*x_lq+b[1]

        if self.mtn_prior:
            if z_mtn is None:
                raise ValueError("mtn_prior=True이면 z_mtn을 함께 넘겨야 합니다.")
            z_ls = z_ls + self.kappa * z_mtn

        return z_ls, z_lq

    def forward(self,pi_ls,pi_lq,z_mtn=None):
        z_ls, z_lq = self.z(pi_ls, pi_lq, z_mtn)

        log_p_ls,log_q_ls=F.logsigmoid(z_ls),F.logsigmoid(-z_ls)
        log_p_lq,log_q_lq=F.logsigmoid(z_lq),F.logsigmoid(-z_lq)

        result=[] #w00,w10,w01,w11 담을 배열
        for ls,lq in LATENT_STATES:
            w=ls*log_p_ls+(1-ls)*log_q_ls+lq*log_p_lq+(1-lq)*log_q_lq
            result.append(w)

        return torch.stack(result,dim=-1)


class AreaPrior(nn.Module):
    """후속실험 3의 면적 항 prior. 지시서 §2-1 B 계열이다.

        z_LS = link(pi_LS) + log k_LS + b_LS  (+ kappa * m)
        z_LQ = link(pi_LQ) + log k_LQ                  (학습 없음)

    USGS 값 pi는 발생확률이 아니라 격자 한 칸에서 덮이는 면적 비율이다.
    칸끼리 독립이면 시정촌에서 한 곳이라도 날 기대 칸 수가
        lambda = pi * k,   k = 시정촌 총면적 / 칸 넓이
    라서 log lambda = log pi + log k 가 된다. 그래서 a = c = 1로 고정한다.

    link
    ----
    "log"   : log(pi) + log k. (기본값)
              유도식 log lambda = log pi + log k 그대로이고, 기존 면적 항 브랜치
              (followup3-area-avg-*)가 쓰던 것과 같다.
    "logit" : 지시서 §2-1 B의 표기대로 logit(pi) + log k.

    지시서 §2-1 B는 logit으로 적혀 있으나 기존 브랜치는 log였다. 둘 다 돌려본 결과
    LS는 순위가 한 자리도 다르지 않았고(가중 AUC 0.8550 동일) LQ만 log가 앞서
    (0.7812 vs 0.7768) log를 주 조건으로 쓰기로 정했다. logit은 민감도로 남긴다.

    b_LS는 [b_min, b_max] 안에서만 학습한다(기본 [-2, 4], 초기값 0).
    clamp는 경계에서 gradient가 0이 되므로 기존 Prior와 같은 sigmoid 재파라미터화를 쓴다.
    fix_b=True이면 b_LS도 0으로 고정해 학습 파라미터가 하나도 없는 기준선(B0)이 된다.
    """

    LINKS = ("logit", "log")

    def __init__(self, *, b_min: float = -2.0, b_max: float = 4.0,
                 fix_b: bool = False, mtn_prior: bool = False, link: str = "log"):
        super().__init__()

        if link not in self.LINKS:
            raise ValueError(f"link는 {self.LINKS} 중 하나여야 합니다: {link}")
        self.link = link
        self.mode = "area"
        self.fix_b = bool(fix_b)
        self.mtn_prior = bool(mtn_prior)

        b_min, b_max = float(b_min), float(b_max)
        if not b_min < 0.0 < b_max:
            raise ValueError(f"b 범위는 초기값 0을 안쪽에 포함해야 합니다: [{b_min}, {b_max}]")
        self.B_MIN, self.B_MAX = b_min, b_max

        if self.fix_b:
            # buffer는 optimizer가 잡아가지 않으므로 학습되지 않는다.
            self.register_buffer("b_ls", torch.zeros(1, dtype=DTYPE))
        else:
            b_init = _inverse_sigmoid((0.0 - b_min) / (b_max - b_min))
            self._b_raw = nn.Parameter(torch.full((1,), b_init, dtype=DTYPE))

        if self.mtn_prior:
            self.kappa = nn.Parameter(torch.zeros(1, dtype=DTYPE))

    @property
    def b_value(self) -> Tensor:
        """실제 식에 들어가는 b_LS 스칼라. b_LQ는 항상 0이다."""
        if self.fix_b:
            return self.b_ls
        return self.B_MIN + (self.B_MAX - self.B_MIN) * torch.sigmoid(self._b_raw)

    def _link(self, pi):
        if self.link == "logit":
            return torch.logit(pi, eps=EPS)
        # log(0)을 피하려고 기존 logit과 같은 EPS로 아래를 자른다.
        return torch.log(pi.clamp_min(EPS))

    def z(self, pi_ls, pi_lq, log_k_ls, log_k_lq, z_mtn=None):
        """z_LS, z_LQ [B]."""
        z_ls = self._link(pi_ls) + log_k_ls + self.b_value
        z_lq = self._link(pi_lq) + log_k_lq

        if self.mtn_prior:
            if z_mtn is None:
                raise ValueError("mtn_prior=True이면 z_mtn을 함께 넘겨야 합니다.")
            z_ls = z_ls + self.kappa * z_mtn

        return z_ls, z_lq

    def forward(self, pi_ls, pi_lq, log_k_ls, log_k_lq, z_mtn=None):
        z_ls, z_lq = self.z(pi_ls, pi_lq, log_k_ls, log_k_lq, z_mtn)

        log_p_ls, log_q_ls = F.logsigmoid(z_ls), F.logsigmoid(-z_ls)
        log_p_lq, log_q_lq = F.logsigmoid(z_lq), F.logsigmoid(-z_lq)

        result = []  # w00, w10, w01, w11
        for ls, lq in LATENT_STATES:
            result.append(ls * log_p_ls + (1 - ls) * log_q_ls + lq * log_p_lq + (1 - lq) * log_q_lq)
        return torch.stack(result, dim=-1)


def prior_z(pri, batch):
    """Prior / AreaPrior 어느 쪽이든 batch에서 (z_LS, z_LQ)를 만든다."""
    z_mtn = batch.z_mtn if getattr(pri, "mtn_prior", False) else None
    if isinstance(pri, AreaPrior):
        return pri.z(batch.pi_ls, batch.pi_lq, batch.log_k_ls, batch.log_k_lq, z_mtn)
    return pri.z(batch.pi_ls, batch.pi_lq, z_mtn)


def prior_log_w(pri, batch):
    """Prior / AreaPrior 어느 쪽이든 batch에서 4상태 log prior [B, 4]를 만든다."""
    z_mtn = batch.z_mtn if getattr(pri, "mtn_prior", False) else None
    if isinstance(pri, AreaPrior):
        return pri(batch.pi_ls, batch.pi_lq, batch.log_k_ls, batch.log_k_lq, z_mtn)
    return pri(batch.pi_ls, batch.pi_lq, z_mtn)
