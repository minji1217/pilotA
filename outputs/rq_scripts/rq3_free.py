"""γ ≥ 0 제약(softplus)을 푼 AdminDER (2026-11-14, 사용자 요청).

repo 코드는 고치지 않고, 이 스크립트 안에서만 DamageRegression의 γ를 softplus 없이 그대로 쓰게 바꾼다.
- γ = 내부 파라미터 그대로 (음수 가능). 초기값 0.1은 같음 (_inverse_softplus를 항등으로).
- 나머지는 최종 설정 그대로: λ_γ = λ_κ = 10 (Σγ²는 실제 γ에 걸림), 3000 에폭, 산사태 라벨 학습, 액상화 라벨 미사용, LQ b-only.
주의: Adam은 파라미터 공간에서 움직이므로, 제약이 안 걸린 채널도 softplus 판과 학습 경로가 달라진다(3000 에폭 미수렴이라 결과가 조금 다를 수 있음).

실행 (repo 폴더에서):
  python rq3_free.py full                          # 9개 지진 전체 학습 → outputs/rq3/free/gamma_full9_free.csv
  python rq3_free.py loeo <지진 이름...>           # LOEO → outputs/holdout_summary_free_<지진>.csv
  python rq3_free.py boot <worker> <n_workers> <B> # 부트스트랩 (rq3_bootstrap.py와 같은 재표집·난수) → outputs/rq3/free/bootstrap/b####.csv
"""
import contextlib
import io
import sys
import time
from pathlib import Path

REPO = r"C:\Users\PC\Desktop\pilotA"
sys.path.insert(0, REPO)
sys.path.insert(0, str(Path(__file__).parent))
sys.stdout.reconfigure(encoding="utf-8")
import numpy as np
import pandas as pd
import torch

import regression

regression._inverse_softplus = lambda v: float(v)
regression.DamageRegression.gamma_ls = property(lambda self: self._gamma_ls_unconstrained)
regression.DamageRegression.gamma_lq = property(lambda self: self._gamma_lq_unconstrained)

from train import GT_PATH, STATS_PATH, USGS_PATH, report_holdout, train
from loader import attach_ls_labels, load_eval_ground_truth, load_pilot_a_batch, subset_batch
from marginal import marginalize
from infer import infer
from prior import prior_log_w
from schema import CHANNELS, EVENT_TO_INDEX

OUT = Path(REPO) / "outputs" / "rq3" / "free"
OUT.mkdir(parents=True, exist_ok=True)
CFG = dict(seed=0, epochs=3000, lr=0.02, lam_gamma=10.0, area_mode="fixed-cov-mtn", lam_kappa=10.0,
           mtn_standardize="train", reg_mtn=False, lq_mtn=False, lq_b_only=True, use_labels=True, lq_labels=False)


def fit(b, quiet=True):
    with contextlib.redirect_stdout(io.StringIO()) if quiet else contextlib.nullcontext():
        reg, like, pri, hist = train(batch=b, **CFG)
    # 패치가 실제로 적용됐는지: γ가 내부 파라미터 그 자체여야 함
    assert reg.gamma_ls is reg._gamma_ls_unconstrained and reg.gamma_lq is reg._gamma_lq_unconstrained
    return reg, like, pri, hist


def gamma_df(reg, **extra):
    return pd.DataFrame({**extra, "channel": CHANNELS, "gamma_ls": reg.gamma_ls.detach().numpy(),
                         "gamma_lq": reg.gamma_lq.detach().numpy()})


batch = load_pilot_a_batch(STATS_PATH, USGS_PATH)
batch = attach_ls_labels(GT_PATH, batch, load_eval_ground_truth(GT_PATH, batch))
assert batch.batch_size == 418
mode = sys.argv[1]

if mode == "full":
    torch.set_num_threads(4)
    reg, like, pri, hist = fit(batch)
    d = gamma_df(reg)
    d["final_loss"] = float(hist.loss_total.iloc[-1])
    d.to_csv(OUT / "gamma_full9_free.csv", index=False)
    hist.to_csv(OUT / "loss_full9_free.csv", index=False)
    print(d.to_string(index=False))

elif mode == "loeo":
    torch.set_num_threads(2)
    for ev in sys.argv[2:]:
        t0 = time.time()
        ho = EVENT_TO_INDEX[ev]
        reg, like, pri, hist = fit(subset_batch(batch, batch.event_idx != ho))
        with torch.no_grad():
            out_r = reg(batch)
            log_joint, log_Py = marginalize(prior_log_w(pri, batch), like(batch, out_r.mu).log_L)
            p_ls, p_lq = infer(log_joint, log_Py)
        name = ev.replace(" ", "")
        with contextlib.redirect_stdout(io.StringIO()):
            report_holdout(batch, reg, like, pri, p_ls, p_lq, ev, f"_free_{name}")
        gamma_df(reg).to_csv(OUT / f"gamma_loeo_{name}.csv", index=False)
        print(f"[free] {ev} 끝 {time.time() - t0:.0f}s", flush=True)

elif mode == "boot":
    from rq3_bootstrap_lib import stratified_idx, take_rows
    w, nw, B = map(int, sys.argv[2:5])
    torch.set_num_threads(2)
    bo = OUT / "bootstrap"
    bo.mkdir(exist_ok=True)
    for b in range(w, B, nw):
        f = bo / f"b{b:04d}.csv"
        if f.exists():
            continue
        t0 = time.time()
        idx = stratified_idx(batch, b)
        ref = np.load(Path(REPO) / "outputs/rq3/bootstrap" / f"idx_b{b:04d}.npy")
        assert np.array_equal(idx, ref), b  # 제약 판과 같은 시정촌 표본
        reg, _, _, hist = fit(take_rows(batch, idx))
        d = gamma_df(reg, b=b)
        d["final_loss"] = float(hist.loss_total.iloc[-1])
        d.to_csv(f, index=False)
        print(f"b{b} {time.time() - t0:.0f}s", flush=True)
