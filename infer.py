from torch import Tensor
from torch import exp
import torch
def infer(log_joint:Tensor, log_Py: Tensor):
    """
    학습되는 파라미터 없이 오로지 순수 수학
    P(Ls=1|파라미터) , P(Lq=1|파라미터)
    """

    log_p_ls=torch.logsumexp(log_joint[:,[1,3]],dim=-1)/log_Py
    log_p_lq=torch.logsumexp(log_joint[:,[2,3]],dim=-1)/log_Py

    return exp(log_p_ls),exp(log_p_lq)