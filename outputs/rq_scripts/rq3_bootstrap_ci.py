"""RQ3 부트스트랩 결과(outputs/rq3/bootstrap/b*.csv)로 배율 exp(γ)의 95% 퍼센타일 구간을 낸다.
점추정은 원래 418행으로 학습한 outputs/rq3/gamma_full9.csv (엑셀 RQ3 표와 같은 값).
출력: outputs/rq3/bootstrap_ci.csv
"""
import glob
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(r"C:\Users\PC\Desktop\pilotA")
files = sorted(glob.glob(str(REPO / "outputs/rq3/bootstrap/b*.csv")))
df = pd.concat([pd.read_csv(f) for f in files])
assert len(files) == 1000, len(files)
assert (df.groupby("b").size() == 6).all() and df.b.nunique() == 1000
assert df[["gamma_ls", "gamma_lq"]].notna().all().all()

ref = pd.read_csv(REPO / "outputs/rq3/gamma_full9.csv").set_index("channel")
rows = []
for hz, col in (("LS", "gamma_ls"), ("LQ", "gamma_lq")):
    for ch in ref.index:
        g = df.loc[df.channel == ch, col].to_numpy()
        lo, hi = np.percentile(g, [2.5, 97.5])
        rows.append({"재해": hz, "channel": ch, "label": ref.loc[ch, "label"],
                     "gamma": ref.loc[ch, col], "배율": np.exp(ref.loc[ch, col]),
                     "배율_2.5%": np.exp(lo), "배율_97.5%": np.exp(hi),
                     "배율_부트스트랩_중앙값": np.exp(np.median(g)),
                     "gamma_부트스트랩_sd": g.std(ddof=1)})
out = pd.DataFrame(rows)
out.to_csv(REPO / "outputs/rq3/bootstrap_ci.csv", index=False, encoding="utf-8-sig")
print("회차", len(files), "· 최종 손실 범위", round(df.final_loss.min(), 1), "~", round(df.final_loss.max(), 1))
print(out.to_string(index=False, float_format=lambda v: f"{v:.3f}"))
