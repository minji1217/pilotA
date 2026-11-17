"""RQ4 균등 prior 변형 2개 (언니 run_ablation.py의 uniform_prior / uniform_learned와 같은 방식).

  umean  : 재해마다, 학습 행의 원래 사전확률(κ = 0, b = 0일 때)을 평균한 값 하나로 고정
  ulearn : 위 평균에서 출발해 재해마다 상수 하나를 학습
(0.5 고정은 rq4_run_nolq.py의 uniform 조건)

repo 코드는 고치지 않는다. train 모듈의 AreaPrior를 균등 prior 하위 클래스로 바꿔 끼운다.
설정은 TRACE 최종(산사태 라벨 학습, 액상화 라벨 미사용, LQ b-only), λ_γ = λ_κ = 10, 3000 에폭, seed 0.

실행: (repo 폴더에서) python <이 파일> <umean|ulearn> <all9|dpm5>
  all9 : 9개 지진 LOEO, 평가 지진 빼고 나머지 8개로 학습
  dpm5 : DPM 있는 5개 지진 LOEO, 나머지 4개로 학습
"""
import sys
import time

REPO = r"C:\Users\PC\Desktop\pilotA"
sys.path.insert(0, REPO)

import torch

import train as T
from loader import attach_ls_labels, load_eval_ground_truth, load_pilot_a_batch, subset_batch
from marginal import marginalize
from infer import infer
from prior import prior_log_w
from schema import EPS, EVENT_TO_INDEX, EVENTS

cond, scope = sys.argv[1], sys.argv[2]
assert cond in ("umean", "ulearn") and scope in ("all9", "dpm5")
DPM5 = ["2016 구마모토", "2018 오사카", "2018 훗카이도", "2021 후쿠시마", "2024 노토반도"]
ORIG_PRIOR = T.AreaPrior


class PriorUniform(ORIG_PRIOR):
    """모든 시정촌에 같은 로짓 C + u_shift. 산사태·액상화를 똑같이 처리한다."""
    C = (0.0, 0.0)
    LEARN = False

    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        self.u_shift = torch.nn.Parameter(torch.zeros(2, dtype=torch.float64), requires_grad=self.LEARN)

    def z(self, pi_ls, *args, **kw):
        zero = torch.zeros_like(pi_ls)
        return zero + self.C[0] + self.u_shift[0], zero + self.C[1] + self.u_shift[1]


def uniform_const(batch, t):
    """학습 행의 원래 사전확률(κ = 0, b = 0)의 평균 → 로짓. 모델 식 그대로(log p̄는 EPS로 자름)."""
    z_ls = torch.log(batch.pi_ls.clamp_min(EPS)) + batch.log_k_ls + batch.log_cov_ls
    z_lq = torch.log(batch.pi_lq.clamp_min(EPS)) + (batch.log_k_lq - batch.log_k_lq[t].mean())
    p_ls, p_lq = torch.sigmoid(z_ls[t]).mean(), torch.sigmoid(z_lq[t]).mean()
    return float(torch.logit(p_ls)), float(torch.logit(p_lq)), float(p_ls), float(p_lq)


T.AreaPrior = PriorUniform
PriorUniform.LEARN = cond == "ulearn"

batch = load_pilot_a_batch(T.STATS_PATH, T.USGS_PATH)
batch = attach_ls_labels(T.GT_PATH, batch, load_eval_ground_truth(T.GT_PATH, batch))
events = DPM5 if scope == "dpm5" else list(EVENTS)
in_dpm5 = torch.isin(batch.event_idx, torch.tensor([EVENT_TO_INDEX[e] for e in DPM5]))
tag = "rq4d5" if scope == "dpm5" else "rq4nl"

for ev in events:
    t0 = time.time()
    ho = EVENT_TO_INDEX[ev]
    train_mask = batch.event_idx != ho
    if scope == "dpm5":
        train_mask = train_mask & in_dpm5
    c_ls, c_lq, p_ls0, p_lq0 = uniform_const(batch, train_mask)
    PriorUniform.C = (c_ls, c_lq)
    reg, like, pri, hist = T.train(
        batch=subset_batch(batch, train_mask), seed=0, epochs=3000, lr=0.02, lam_gamma=10.0,
        area_mode="fixed-cov-mtn", lam_kappa=10.0, mtn_standardize="train",
        reg_mtn=False, use_labels=True, lq_labels=False, lq_mtn=False, lq_b_only=True,
    )
    with torch.no_grad():
        out_r = reg(batch)
        out_l = like(batch, out_r.mu)
        log_joint, log_Py = marginalize(prior_log_w(pri, batch), out_l.log_L)
        p_ls, p_lq = infer(log_joint, log_Py)
    sfx = f"_{tag}_{cond}_{ev.replace(' ', '')}"
    T.report_holdout(batch, reg, like, pri, p_ls, p_lq, ev, sfx)
    sh = pri.u_shift.detach()
    q_ls = float(torch.sigmoid(torch.tensor(c_ls) + sh[0]))
    q_lq = float(torch.sigmoid(torch.tensor(c_lq) + sh[1]))
    print(f"[{cond}/{scope}] {ev} 끝 {time.time() - t0:.0f}s  학습행 {int(train_mask.sum())}  "
          f"출발 사전확률 LS {p_ls0:.4f} LQ {p_lq0:.4f}  최종 LS {q_ls:.4f} LQ {q_lq:.4f}", flush=True)
