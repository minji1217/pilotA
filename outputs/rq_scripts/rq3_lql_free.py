"""γ ≥ 0 제약(softplus)을 푼 AdminDER — 액상화 라벨 포함판 (2026-11-17, 교수님 요청: 저널 확장용으로 확보).

rq3_free.py와 같고 액상화 라벨 학습만 켬. 출력 outputs/rq3/lql_free/.

repo 코드는 고치지 않고, 이 스크립트 안에서만 DamageRegression의 γ를 softplus 없이 그대로 쓰게 바꾼다.
- γ = 내부 파라미터 그대로 (음수 가능). 초기값 0.1은 같음 (_inverse_softplus를 항등으로).
- 나머지는 최종 설정 그대로: λ_γ = λ_κ = 10 (Σγ²는 실제 γ에 걸림), 3000 에폭, 산사태·액상화 라벨 학습, LQ b-only.
주의: Adam은 파라미터 공간에서 움직이므로, 제약이 안 걸린 채널도 softplus 판과 학습 경로가 달라진다(3000 에폭 미수렴이라 결과가 조금 다를 수 있음).

실행 (repo 폴더에서):
  python rq3_lql_free.py full                          # 9개 지진 전체 학습 → outputs/rq3/lql_free/gamma_full9_free.csv
  python rq3_lql_free.py loeo <지진 이름...>           # LOEO → outputs/holdout_summary_lqlfree_<지진>.csv
  python rq3_lql_free.py boot <worker> <n_workers> <B> # 부트스트랩 (rq3_bootstrap.py와 같은 재표집·난수) → outputs/rq3/lql_free/bootstrap/b####.csv
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

OUT = Path(REPO) / "outputs" / "rq3" / "lql_free"
OUT.mkdir(parents=True, exist_ok=True)
CFG = dict(seed=0, epochs=3000, lr=0.02, lam_gamma=10.0, area_mode="fixed-cov-mtn", lam_kappa=10.0,
           mtn_standardize="train", reg_mtn=False, lq_mtn=False, lq_b_only=True, use_labels=True, lq_labels=True)


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
            report_holdout(batch, reg, like, pri, p_ls, p_lq, ev, f"_lqlfree_{name}")
        gamma_df(reg).to_csv(OUT / f"gamma_loeo_{name}.csv", index=False)
        print(f"[lqlfree] {ev} 끝 {time.time() - t0:.0f}s", flush=True)

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

elif mode == "ci":
    import glob
    files = sorted(glob.glob(str(OUT / "bootstrap" / "b*.csv")))
    df = pd.concat([pd.read_csv(f) for f in files])
    assert len(files) == 1000, len(files)
    assert (df.groupby("b").size() == 6).all() and df.b.nunique() == 1000
    assert df[["gamma_ls", "gamma_lq"]].notna().all().all()
    ref = pd.read_csv(OUT / "gamma_full9_free.csv").set_index("channel")
    lab = pd.read_csv(Path(REPO) / "outputs/rq3/gamma_full9.csv").set_index("channel").label
    rows = []
    for hz, col in (("LS", "gamma_ls"), ("LQ", "gamma_lq")):
        for ch in ref.index:
            g = df.loc[df.channel == ch, col].to_numpy()
            lo, hi = np.percentile(g, [2.5, 97.5])
            rows.append({"재해": hz, "channel": ch, "label": lab[ch], "gamma": ref.loc[ch, col],
                         "배율": np.exp(ref.loc[ch, col]), "배율_2.5%": np.exp(lo), "배율_97.5%": np.exp(hi),
                         "배율_부트스트랩_중앙값": np.exp(np.median(g)), "gamma_부트스트랩_sd": g.std(ddof=1),
                         "gamma<0_비율": (g < 0).mean()})
    out = pd.DataFrame(rows)
    out.to_csv(OUT / "bootstrap_ci_lql_free.csv", index=False, encoding="utf-8-sig")
    print("회차", len(files), "· 최종 손실 범위", round(df.final_loss.min(), 1), "~", round(df.final_loss.max(), 1))
    print(out.to_string(index=False, float_format=lambda v: f"{v:.3f}"))
