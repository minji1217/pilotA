from torch import Tensor
from torch import exp
import torch

from data.schema import LATENT_STATES

LS_ON=[i for i,(ls,lq) in enumerate(LATENT_STATES) if ls==1]
LQ_ON=[i for i,(ls,lq) in enumerate(LATENT_STATES) if lq==1]

def infer(log_joint:Tensor, log_Py: Tensor):
    """
    학습되는 파라미터 없이 오로지 순수 수학
    P(Ls=1|파라미터) , P(Lq=1|파라미터)

    입력:  log_joint [B,4], log_Py [B]
    출력:  p_ls [B], p_lq [B]
    """

    log_p_ls=torch.logsumexp(log_joint[:,LS_ON],dim=-1)/log_Py
    log_p_lq=torch.logsumexp(log_joint[:,LQ_ON],dim=-1)/log_Py

    return exp(log_p_ls),exp(log_p_lq)