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


# 후속실험 4: LS 라벨이 있는 행은 LS를 라벨 값으로 고정하고 LQ만 합한다.
#   라벨 있음  log L_i = log Σ_q       P(LS=ℓ_i) P(LQ=q) p(y_i | ℓ_i, q)
#   라벨 없음  log L_i = log Σ_s Σ_q   P(LS=s)   P(LQ=q) p(y_i | s, q)
# 액상화 라벨도 주면 같은 방식으로 LQ를 고정한다. 둘 다 있는 행은 상태 하나만 남는다.
_STATE_LS = torch.tensor([ls for ls, _ in LATENT_STATES])
_STATE_LQ = torch.tensor([lq for _, lq in LATENT_STATES])

def marginalize_labeled(log_w, log_L, ls_label, ls_label_mask, lq_label=None, lq_label_mask=None):
    log_wl = log_w + log_L
    # 라벨과 LS가 다른 상태는 합에서 뺀다(-inf). 라벨 없는 행은 네 상태 모두 남는다.
    wrong = ls_label_mask.unsqueeze(-1) & (_STATE_LS.unsqueeze(0) != ls_label.unsqueeze(-1))
    if lq_label is not None:
        wrong = wrong | (lq_label_mask.unsqueeze(-1) & (_STATE_LQ.unsqueeze(0) != lq_label.unsqueeze(-1)))
    log_Py = torch.logsumexp(log_wl.masked_fill(wrong, float("-inf")), dim=-1)
    return log_wl, log_Py