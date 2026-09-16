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
                 b_min=None, b_max=None, **kwargs):
        super().__init__(*args, **kwargs)

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

    def z(self, pi_ls, pi_lq):
        """z_ls, z_lq [B]. 평가에서 '자기 prior' 단독 점수로 쓴다.

        a>0이고 b는 상수라 이 z의 순위는 pi와 같다. 그래도 AreaPrior와 같은
        방식으로 기록해 두어야 두 계열의 결과 CSV를 같은 열로 비교할 수 있다.
        """
        a, b = self.a_value, self.b_value
        return (a[0] * torch.logit(pi_ls, eps=EPS) + b[0],
                a[1] * torch.logit(pi_lq, eps=EPS) + b[1])

    def forward(self,pi_ls,pi_lq):
        x_ls=torch.logit(pi_ls,eps=EPS)
        x_lq=torch.logit(pi_lq,eps=EPS)

        a, b = self.a_value, self.b_value

        z_ls=a[0]*x_ls+b[0]
        z_lq=a[1]*x_lq+b[1]

        log_p_ls,log_q_ls=F.logsigmoid(z_ls),F.logsigmoid(-z_ls)
        log_p_lq,log_q_lq=F.logsigmoid(z_lq),F.logsigmoid(-z_lq)

        result=[] #w00,w10,w01,w11 담을 배열
        for ls,lq in LATENT_STATES:
            w=ls*log_p_ls+(1-ls)*log_q_ls+lq*log_p_lq+(1-lq)*log_q_lq
            result.append(w)

        return torch.stack(result,dim=-1)


class AreaPrior(nn.Module):
    """후속실험 3: 시정촌 면적 항을 넣은 prior.

        z = a·log(p̄) + b + c·log k        (LS, LQ 각각 a, b, c를 따로 둔다)

    USGS 값 p̄(시정촌 평균집계)는 칸 면적 중 덮일 비율이다. 칸끼리 독립이면
        P(시정촌에서 한 곳이라도) = 1 − ∏(1 − p_i) ≈ 1 − exp(−λ),   λ = p̄ × k
    이다. 확률로 넣으면 λ가 클 때 1에 붙어 순위가 사라지므로(포화)
    logit(P) 대신 순위가 같은 log λ = log p̄ + log k 를 쓴다.
    그래서 a = 1, b = 0, c = 1 이 유도식 그대로다. logit(p̄)가 아니라 log(p̄)다.

    mode (브랜치 followup3-area-avg-<mode>)
    ----
    "fixed"  : a=1, b=0, c=1 고정. 유도식 그대로(기준).
    "tied"   : c=a로 묶고 a, b 학습. z = a·log λ + b 라서 순위는 fixed와 같고 확률 수준만 학습한다.
    "bounded": c=1 고정, a, b 학습.
    "free"   : a, b, c 모두 학습.
    "a1-c05" : a=1, b=0, c=0.5 고정. 넓은 곳을 감점한다.
    "a1-c2"  : a=1, b=0, c=2 고정. 넓은 곳에 가산점을 준다.

    학습하는 값은 기존 Prior처럼 sigmoid 재파라미터화로 범위를 지킨다.
    a ∈ [0.5, 2], b ∈ [b_min, b_max](기본 [-2, 4]), c ∈ [c_min, c_max](기본 [0, 2]).
    초기값은 a=1, b=0, c=1이다.
    """

    MODES = ("fixed", "tied", "bounded", "free", "a1-c05", "a1-c2")
    # c를 학습하지 않는 모드의 c 값. tied는 c=a라서 여기 없다.
    FIXED_C = {"fixed": 1.0, "bounded": 1.0, "a1-c05": 0.5, "a1-c2": 2.0}

    A_MIN, A_MAX = 0.5, 2.0

    def __init__(self, mode: str = "fixed", b_min: float = -2.0, b_max: float = 4.0,
                 c_min: float = 0.0, c_max: float = 2.0):
        super().__init__()
        if mode not in self.MODES:
            raise ValueError(f"mode는 {self.MODES} 중 하나여야 합니다: {mode}")
        self.mode = mode

        b_min, b_max, c_min, c_max = float(b_min), float(b_max), float(c_min), float(c_max)
        if not b_min < 0.0 < b_max:
            raise ValueError(f"b 범위는 초기값 0을 안쪽에 포함해야 합니다: [{b_min}, {b_max}]")
        if not c_min < 1.0 < c_max:
            raise ValueError(f"c 범위는 초기값 1을 안쪽에 포함해야 합니다: [{c_min}, {c_max}]")
        self.B_MIN, self.B_MAX = b_min, b_max
        self.C_MIN, self.C_MAX = c_min, c_max

        self.learn_ab = mode in ("tied", "bounded", "free")
        if self.learn_ab:
            a_init = _inverse_sigmoid((1.0 - self.A_MIN) / (self.A_MAX - self.A_MIN))
            b_init = _inverse_sigmoid((0.0 - b_min) / (b_max - b_min))
            self._a_raw = nn.Parameter(torch.full((2,), a_init, dtype=DTYPE))
            self._b_raw = nn.Parameter(torch.full((2,), b_init, dtype=DTYPE))
        else:
            # buffer는 optimizer가 잡아가지 않으므로 학습되지 않는다.
            self.register_buffer("a", torch.ones(2, dtype=DTYPE))
            self.register_buffer("b", torch.zeros(2, dtype=DTYPE))

        if mode == "free":
            c_init = _inverse_sigmoid((1.0 - c_min) / (c_max - c_min))
            self._c_raw = nn.Parameter(torch.full((2,), c_init, dtype=DTYPE))
        elif mode in self.FIXED_C:
            self.register_buffer("c", torch.full((2,), self.FIXED_C[mode], dtype=DTYPE))

    @staticmethod
    def _scale(raw: Tensor, lo: float, hi: float) -> Tensor:
        return lo + (hi - lo) * torch.sigmoid(raw)

    @property
    def a_value(self) -> Tensor:
        """실제 식에 들어가는 a [2]. LS=0, LQ=1."""
        return self._scale(self._a_raw, self.A_MIN, self.A_MAX) if self.learn_ab else self.a

    @property
    def b_value(self) -> Tensor:
        """실제 식에 들어가는 b [2]. LS=0, LQ=1."""
        return self._scale(self._b_raw, self.B_MIN, self.B_MAX) if self.learn_ab else self.b

    @property
    def c_value(self) -> Tensor:
        """실제 식에 들어가는 c [2]. LS=0, LQ=1."""
        if self.mode == "tied":
            return self.a_value
        if self.mode == "free":
            return self._scale(self._c_raw, self.C_MIN, self.C_MAX)
        return self.c

    def z(self, pi_ls, pi_lq, log_k_ls, log_k_lq):
        """z_ls, z_lq [B]. 평가에서 '자기 prior' 단독 점수로도 쓴다."""
        # p̄ = 0인 행이 있어 log 0을 피하려고 기존 logit과 같은 EPS로 아래를 자른다.
        x_ls = torch.log(pi_ls.clamp_min(EPS))
        x_lq = torch.log(pi_lq.clamp_min(EPS))
        a, b, c = self.a_value, self.b_value, self.c_value
        z_ls = a[0] * x_ls + b[0] + c[0] * log_k_ls
        z_lq = a[1] * x_lq + b[1] + c[1] * log_k_lq
        return z_ls, z_lq

    def forward(self, pi_ls, pi_lq, log_k_ls, log_k_lq):
        z_ls, z_lq = self.z(pi_ls, pi_lq, log_k_ls, log_k_lq)

        log_p_ls, log_q_ls = F.logsigmoid(z_ls), F.logsigmoid(-z_ls)
        log_p_lq, log_q_lq = F.logsigmoid(z_lq), F.logsigmoid(-z_lq)

        result = []  # w00, w10, w01, w11
        for ls, lq in LATENT_STATES:
            result.append(ls * log_p_ls + (1 - ls) * log_q_ls + lq * log_p_lq + (1 - lq) * log_q_lq)
        return torch.stack(result, dim=-1)


def prior_log_w(pri, batch):
    """Prior / AreaPrior 어느 쪽이든 batch에서 4상태 log prior [B, 4]를 만든다."""
    if isinstance(pri, AreaPrior):
        return pri(batch.pi_ls, batch.pi_lq, batch.log_k_ls, batch.log_k_lq)
    return pri(batch.pi_ls, batch.pi_lq)
