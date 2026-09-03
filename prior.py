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

    "bounded" : a in [0.5, 2], b in [-2, 2] 범위 안에서만 학습한다.
                clamp는 경계에서 gradient가 0이 되어 학습이 멈추므로
                sigmoid 재파라미터화를 쓴다. 초기값은 정확히 a=1, b=0이다.
    """

    MODES = ("free", "fixed", "bounded")

    A_MIN, A_MAX = 0.5, 2.0
    B_MIN, B_MAX = -2.0, 2.0

    def __init__(self, *args, mode: str = "free", b_bound: float = 2.0, **kwargs):
        super().__init__(*args, **kwargs)

        if mode not in self.MODES:
            raise ValueError(f"mode는 {self.MODES} 중 하나여야 합니다: {mode}")
        if b_bound <= 0:
            raise ValueError(f"b_bound는 0보다 커야 합니다: {b_bound}")
        self.mode = mode

        # 실험에서 b가 상한에 계속 붙어 나와 범위를 조절할 수 있게 인스턴스 값으로 둔다.
        self.B_MIN, self.B_MAX = -float(b_bound), float(b_bound)

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
