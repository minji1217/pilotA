import torch
from schema import LATENT_STATES

# marginal(주변화)는 이제 민지님께서 likeligood.py에서 전달 해주신 L=[B,4]를
# 내가 만든 prior.py에서 만들어진 w=[B,4]와 곱하고 다 더하는 작업
# P(y)=w00*L00 + w10*L10 + w01*L01 + w11*L11

def marginalize(log_w, log_L):
    log_wl=log_w+log_L
    log_Py=torch.logsumexp(log_wl,dim=-1)
    return log_wl,log_Py

#민망할 정도로 짧다...