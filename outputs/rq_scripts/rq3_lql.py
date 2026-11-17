"""RQ3 γ — 원고 설정(산사태·액상화 라벨 모두 학습)판. 2026-11-17 사용자 요청.

기존 RQ3(rq3_full_gamma.py, rq3_bootstrap.py)과 모든 설정이 같고 lq_labels=True만 다름:
λ_γ = λ_κ = 10, 3000 에폭, lr 0.02, seed 0, fixed-cov-mtn, LQ b-only, 9개 지진 전체 학습(418행).
재표집도 기존과 같음: 지진별 층화 복원추출, 회차 b 난수 numpy default_rng(b) → 기존 제약판·제약없는판과 회차마다 같은 시정촌.

실행 (어디서든):
  python rq3_lql.py check                         # 원래 418행으로 학습 → 10월 03b labels 파일과 γ 비교, gamma_full9_lql.csv 저장
  python rq3_lql.py run <worker> <n_workers> <B>  # 부트스트랩 회차 worker, worker+n_workers, ... < B
  python rq3_lql.py ci                            # 1000회 모이면 95% 퍼센타일 구간 → bootstrap_ci_lql.csv
출력 폴더: outputs/rq3/lql/
"""
import contextlib
import glob
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

from train import GT_PATH, STATS_PATH, USGS_PATH, train
from loader import attach_ls_labels, load_eval_ground_truth, load_pilot_a_batch
from schema import CHANNELS
from rq3_bootstrap_lib import stratified_idx, take_rows

OUT = Path(REPO) / "outputs" / "rq3" / "lql"
BOOT = OUT / "bootstrap"
BOOT.mkdir(parents=True, exist_ok=True)
KOR = ["사망", "중상", "경상", "전파", "반파", "일부파손"]


def fit(batch):
    with contextlib.redirect_stdout(io.StringIO()):
        reg, like, pri, hist = train(
            batch=batch, seed=0, epochs=3000, lr=0.02, lam_gamma=10.0,
            area_mode="fixed-cov-mtn", lam_kappa=10.0, mtn_standardize="train",
            reg_mtn=False, lq_mtn=False, lq_b_only=True, use_labels=True, lq_labels=True,
        )
    return reg, hist


mode = sys.argv[1]
if mode == "ci":
    files = sorted(glob.glob(str(BOOT / "b*.csv")))
    df = pd.concat([pd.read_csv(f) for f in files])
    assert len(files) == 1000, len(files)
    assert (df.groupby("b").size() == 6).all() and df.b.nunique() == 1000
    assert df[["gamma_ls", "gamma_lq"]].notna().all().all()
    ref = pd.read_csv(OUT / "gamma_full9_lql.csv").set_index("channel")
    rows = []
    for hz, col in (("LS", "gamma_ls"), ("LQ", "gamma_lq")):
        for ch in ref.index:
            g = df.loc[df.channel == ch, col].to_numpy()
            lo, hi = np.percentile(g, [2.5, 97.5])
            rows.append({"재해": hz, "channel": ch, "label": ref.loc[ch, "label"], "gamma": ref.loc[ch, col],
                         "배율": np.exp(ref.loc[ch, col]), "배율_2.5%": np.exp(lo), "배율_97.5%": np.exp(hi),
                         "배율_부트스트랩_중앙값": np.exp(np.median(g)), "gamma_부트스트랩_sd": g.std(ddof=1)})
    out = pd.DataFrame(rows)
    out.to_csv(OUT / "bootstrap_ci_lql.csv", index=False, encoding="utf-8-sig")
    print("회차", len(files), "· 최종 손실 범위", round(df.final_loss.min(), 1), "~", round(df.final_loss.max(), 1))
    print(out.to_string(index=False, float_format=lambda v: f"{v:.3f}"))
    sys.exit()

batch = load_pilot_a_batch(STATS_PATH, USGS_PATH)
batch = attach_ls_labels(GT_PATH, batch, load_eval_ground_truth(GT_PATH, batch))
assert batch.batch_size == 418

if mode == "check":
    torch.set_num_threads(4)
    reg, hist = fit(take_rows(batch, np.arange(batch.batch_size)))
    new = pd.DataFrame({"channel": CHANNELS, "label": KOR, "gamma_ls": reg.gamma_ls.detach().numpy(),
                        "gamma_lq": reg.gamma_lq.detach().numpy()})
    old = pd.read_csv(Path(REPO) / "outputs/언니전달_액상화J_설정/03b_전체판(분리없음)_파라미터_labels.csv")
    for g, col in (("gamma_LS", "gamma_ls"), ("gamma_LQ", "gamma_lq")):
        o = old[old.group == g].set_index("label").value
        new[col + "_oct"] = new.label.map(o)
        print(g, "10월 labels 파일과 max |차이|", float((new[col] - new[col + "_oct"]).abs().max()))
    new["final_loss"] = float(hist.loss_total.iloc[-1])
    new.to_csv(OUT / "gamma_full9_lql.csv", index=False, encoding="utf-8-sig")
    print(new.to_string())
elif mode == "run":
    _, _, w, nw, B = sys.argv
    w, nw, B = int(w), int(nw), int(B)
    torch.set_num_threads(2)
    for b in range(w, B, nw):
        f = BOOT / f"b{b:04d}.csv"
        if f.exists():
            continue
        t0 = time.time()
        idx = stratified_idx(batch, b)
        old_idx = Path(REPO) / "outputs/rq3/bootstrap" / f"idx_b{b:04d}.npy"
        if old_idx.exists():  # 기존 제약판과 같은 시정촌인지 확인
            assert np.array_equal(np.load(old_idx), idx), b
        reg, hist = fit(take_rows(batch, idx))
        pd.DataFrame({"b": b, "channel": CHANNELS, "gamma_ls": reg.gamma_ls.detach().numpy(),
                      "gamma_lq": reg.gamma_lq.detach().numpy(),
                      "final_loss": float(hist.loss_total.iloc[-1])}).to_csv(f, index=False)
        print(f"b{b} {time.time() - t0:.0f}s", flush=True)
