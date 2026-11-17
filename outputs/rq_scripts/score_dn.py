"""언니 DisasterNet 예측(15개 변형 × seed 5)을 TRACE와 같은 평가 시정촌·정답으로 채점한다.

평가 시정촌·정답 = pilotA outputs/holdout_detail_{,lq_}rq4nl_full_<지진>.csv (TRACE RQ1 표와 동일 행)
지진 × 재해 AUC를 seed마다 내고 seed 평균. 가중평균은 평가 시정촌 수로.
예측이 빠진 평가 시정촌이 있거나 값이 NaN이면 멈춘다(추측으로 채우지 않음).
출력: <out_dir>/dn_auc_by_event.csv, dn_auc_weighted.csv
"""
import glob
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")
REPO = Path(r"C:\Users\PC\Desktop\pilotA")
PRED = Path(r"C:\Users\PC\Desktop\학부연구생\DisasterNet\민지언니 전달자료\disasternet_predictions")
OUT = Path(sys.argv[1])
OUT.mkdir(parents=True, exist_ok=True)
EV = {3: "2016 구마모토", 4: "2018 오사카", 5: "2018 훗카이도", 6: "2021 후쿠시마", 7: "2024 노토반도"}
VARS = [  # (단위, 이름, 폴더)
    ("시정촌", "DN", "muni/nobd_DN"), ("시정촌", "SOFT", "muni/nobd_SOFT"), ("시정촌", "DNU", "muni/px_DNU"),
    ("시정촌", "SOFTU", "muni/px_SOFTU"), ("시정촌", "DNU_끄기만", "muni/px_DNU_off"),
    ("시정촌", "DNU_분산만", "muni/px_DNU_var"), ("시정촌", "SOFTU_끄기만", "muni/px_SOFTU_off"),
    ("시정촌", "SOFTU_분산만", "muni/px_SOFTU_var"), ("시정촌", "DN_같은분산0.001", "muni/nobd_DN_cvar001"),
    ("시정촌", "DN_같은분산0.01", "muni/nobd_DN_cvar01"),
    ("칸", "DN", "cells/cells_max_aw"), ("칸", "SOFTU", "cells/cells_max_softunc_paper_aw_mid"),
    ("칸", "SOFTU_끄기만", "cells/cells_max_softunc_off_paper_aw_mid"),
    ("칸", "SOFTU_분산만", "cells/cells_max_softunc_var_paper_aw_mid"),
    ("칸", "LOCALU", "cells/cells_max_local_unc_paper_aw"),
]


def auc(s, y):
    s, y = np.asarray(s, float), np.asarray(y)
    p, n = s[y == 1], s[y == 0]
    if len(p) == 0 or len(n) == 0:
        return np.nan
    d = p[:, None] - n[None, :]
    return float(((d > 0).sum() + 0.5 * (d == 0).sum()) / d.size)


# 평가 행 (TRACE와 동일)
gt = {}
for hz, pat, ycol in (("LS", "holdout_detail_rq4nl_full_*.csv", "ls_true"),
                      ("LQ", "holdout_detail_lq_rq4nl_full_*.csv", "lq_true")):
    d = pd.concat([pd.read_csv(f) for f in glob.glob(str(REPO / "outputs" / pat))])
    d = d[d.event.isin(EV.values())].copy()
    d["code"] = d.muni_code.astype(int).astype(str).str.zfill(5)
    gt[hz] = d[["event", "code", ycol]].rename(columns={ycol: "y"})
print("평가 행:", {k: len(v) for k, v in gt.items()})

rows = []
for unit, name, folder in VARS:
    files = sorted(glob.glob(str(PRED / folder / "predictions_seed*.csv")))
    assert len(files) == 5, (folder, len(files))
    for f in files:
        p = pd.read_csv(f, dtype={"muni_code": str})
        assert len(p) == 264, (f, len(p))
        assert p.muni_code.str.len().eq(5).all(), f
        p["event"] = p.event_idx.map(EV)
        assert p.event.notna().all(), f
        assert not p.duplicated(["event", "muni_code"]).any(), f
        seed = int(p.seed.iloc[0])
        for hz, col in (("LS", "p_ls"), ("LQ", "p_lq")):
            m = gt[hz].merge(p[["event", "muni_code", col]], left_on=["event", "code"],
                             right_on=["event", "muni_code"], how="left")
            if m[col].isna().any():
                raise SystemExit(f"예측 없음/NaN: {folder} seed{seed} {hz}\n{m[m[col].isna()][['event','code']]}")
            for ev, g in m.groupby("event"):
                rows.append({"단위": unit, "변형": name, "폴더": folder, "seed": seed, "재해": hz, "지진": ev,
                             "평가시정촌": len(g), "양성": int(g.y.sum()), "음성": int((g.y == 0).sum()),
                             "AUC": auc(g[col], g.y)})

df = pd.DataFrame(rows)
df = df[df.AUC.notna()]
by_ev = df.groupby(["단위", "변형", "재해", "지진", "평가시정촌", "양성", "음성"], sort=False).AUC.agg(
    ["mean", "min", "max", "count"]).reset_index()
assert (by_ev["count"] == 5).all()
by_ev.to_csv(OUT / "dn_auc_by_event.csv", index=False, encoding="utf-8-sig")

w = []
for (unit, name, hz), g in by_ev.groupby(["단위", "변형", "재해"], sort=False):
    ww = g.평가시정촌
    seedw = df[(df.단위 == unit) & (df.변형 == name) & (df.재해 == hz)].groupby("seed").apply(
        lambda s: (s.AUC * s.평가시정촌).sum() / s.평가시정촌.sum())
    w.append({"단위": unit, "변형": name, "재해": hz, "평가시정촌": int(ww.sum()),
              "가중AUC_seed평균": float((g["mean"] * ww).sum() / ww.sum()),
              "seed별_최소": float(seedw.min()), "seed별_최대": float(seedw.max())})
wdf = pd.DataFrame(w)
wdf.to_csv(OUT / "dn_auc_weighted.csv", index=False, encoding="utf-8-sig")
pd.set_option("display.width", 200)
print(wdf.pivot_table(index=["단위", "변형"], columns="재해", values="가중AUC_seed평균", sort=False).round(4))
print(by_ev[["단위", "변형", "재해", "지진", "평가시정촌", "양성", "음성", "mean"]].to_string())
