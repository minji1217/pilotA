import torch
import torch.nn as nn
from torch import Tensor
import torch.nn.functional as F
from schema import EPS,LATENT_STATES

# 내가 이 파일에서 해야할것
# 1.w를 구하는것 (w00,w10,w01,w11)
# 2.marginalize 주변화는 다른 파일에서 할거여서 지금은 w만들기만
# 3.a*logit(pi)+b

# 민지님께서 만들어 주신 클래스를 통해서 데이터를 USGS 산사태/액상화 가져옴

class Prior(nn.Module):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.a=nn.Parameter(torch.ones(2,dtype=torch.float64))
        self.b=nn.Parameter(torch.zeros(2,dtype=torch.float64))

    def forward(self,pi_ls,pi_lq):
        x_ls=torch.logit(pi_ls,eps=EPS)
        x_lq=torch.logit(pi_lq,eps=EPS)

        z_ls=self.a[0]*x_ls+self.b[0]
        z_lq=self.a[1]*x_lq+self.b[1]

        log_p_ls,log_q_ls=F.logsigmoid(z_ls),F.logsigmoid(-z_ls)
        log_p_lq,log_q_lq=F.logsigmoid(z_lq),F.logsigmoid(-z_lq)

        result=[] #w00,w10,w01,w11 담을 배열
        for ls,lq in LATENT_STATES:
            w=ls*log_p_ls+(1-ls)*log_q_ls+lq*log_p_lq+(1-lq)*log_q_lq
            result.append(w)

        return torch.stack(result,dim=-1)



