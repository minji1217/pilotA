"""RQ3 신뢰구간(교수님 결정 2026-11-13: 부트스트랩).

모델: 9개 지진 전체 학습판, AdminDER 최종 설정 (rq3_full_gamma.py와 같음:
λ_γ = λ_κ = 10, 3000 에폭, 산사태 라벨 학습, 액상화 라벨 미사용, LQ b-only, seed 0).
재표집: 지진마다 그 지진의 시정촌 행 수만큼 복원추출 (지진별 층화). 행에 붙은 피해·라벨·USGS 값은 그대로 따라간다.
회차 b의 재표집 난수는 numpy default_rng(b). 결과는 회차마다 파일 하나라 중간에 끊겨도 이어서 돌릴 수 있다.

실행 (repo 폴더에서):
  python rq3_bootstrap.py check                     # 재표집 없이(원래 418행) 학습 → gamma_full9.csv와 같은지 확인
  python rq3_bootstrap.py run <worker> <n_workers> <B>   # 회차 worker, worker+n_workers, ... < B
출력: outputs/rq3/bootstrap/b<회차>.csv (γ), outputs/rq3/bootstrap/idx_b<회차>.npy (뽑힌 행 번호)
"""
import contextlib
import dataclasses
import io
import sys
import time
from pathlib import Path

REPO = r"C:\Users\PC\Desktop\pilotA"
sys.path.insert(0, REPO)
sys.stdout.reconfigure(encoding="utf-8")
import numpy as np
import pandas as pd
import torch

from train import GT_PATH, STATS_PATH, USGS_PATH, train
from loader import attach_ls_labels, load_eval_ground_truth, load_pilot_a_batch
from schema import CHANNELS

OUT = Path(REPO) / "outputs" / "rq3" / "bootstrap"
OUT.mkdir(parents=True, exist_ok=True)


def take_rows(batch, idx):
    """idx(행 번호, 중복 허용) 순서대로 행을 모은 batch. 모든 필드가 행 단위임을 확인한다."""
    n = batch.batch_size
    changes = {}
    for f in dataclasses.fields(batch):
        v = getattr(batch, f.name)
        if isinstance(v, torch.Tensor):
            assert v.shape[0] == n, f.name
            changes[f.name] = v[torch.as_tensor(idx)]
        elif isinstance(v, tuple):
            assert len(v) == n, f.name
            changes[f.name] = tuple(v[i] for i in idx)
    return dataclasses.replace(batch, **changes)


def stratified_idx(batch, b):
    rng = np.random.default_rng(b)
    ev = batch.event_idx.numpy()
    parts = [rng.choice(np.flatnonzero(ev == e), size=int((ev == e).sum()), replace=True) for e in np.unique(ev)]
    return np.sort(np.concatenate(parts))


def fit(batch):
    with contextlib.redirect_stdout(io.StringIO()):  # 100 에폭마다 찍는 손실 출력 숨김
        reg, like, pri, hist = train(
            batch=batch, seed=0, epochs=3000, lr=0.02, lam_gamma=10.0,
            area_mode="fixed-cov-mtn", lam_kappa=10.0, mtn_standardize="train",
            reg_mtn=False, lq_mtn=False, lq_b_only=True, use_labels=True, lq_labels=False,
        )
    return reg, hist


batch = load_pilot_a_batch(STATS_PATH, USGS_PATH)
batch = attach_ls_labels(GT_PATH, batch, load_eval_ground_truth(GT_PATH, batch))
assert batch.batch_size == 418

if sys.argv[1] == "check":
    torch.set_num_threads(4)
    reg, _ = fit(take_rows(batch, np.arange(batch.batch_size)))
    ref = pd.read_csv(Path(REPO) / "outputs/rq3/gamma_full9.csv")
    d = max(np.abs(reg.gamma_ls.detach().numpy() - ref.gamma_ls).max(),
            np.abs(reg.gamma_lq.detach().numpy() - ref.gamma_lq).max())
    print("재표집 없이 학습한 γ vs gamma_full9.csv  max |차이| =", d)
    assert d < 1e-9
else:
    _, w, nw, B = sys.argv[1:5]
    w, nw, B = int(w), int(nw), int(B)
    torch.set_num_threads(2)
    for b in range(w, B, nw):
        f = OUT / f"b{b:04d}.csv"
        if f.exists():
            continue
        t0 = time.time()
        idx = stratified_idx(batch, b)
        reg, hist = fit(take_rows(batch, idx))
        np.save(OUT / f"idx_b{b:04d}.npy", idx)
        pd.DataFrame({"b": b, "channel": CHANNELS, "gamma_ls": reg.gamma_ls.detach().numpy(),
                      "gamma_lq": reg.gamma_lq.detach().numpy(),
                      "final_loss": float(hist.loss_total.iloc[-1])}).to_csv(f, index=False)
        print(f"b{b} {time.time() - t0:.0f}s", flush=True)
