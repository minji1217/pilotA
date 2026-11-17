"""RQ4 결과 집계. 이벤트 내 AUC를 두 클래스가 있는 이벤트만, 평가 행 수로 가중평균한다.
숫자는 원값에서 한 번만 반올림한다."""
import glob
import sys

import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")
OUT = r"C:\Users\PC\Desktop\pilotA\outputs"
CONDS = ["full", "uniform", "nopgv", "poisson", "noexp", "single"]


def wavg(df, n, col):
    d = df[df[col].notna()]
    return (d[col] * d[n]).sum() / d[n].sum(), int(d[n].sum()), len(d)


rows, per_event = [], []
for c in CONDS:
    files = glob.glob(f"{OUT}/holdout_summary_rq4_{c}_*.csv")
    if not files:
        continue
    df = pd.concat([pd.read_csv(f) for f in files], ignore_index=True)
    df["cond"] = c
    per_event.append(df)
    r = {"cond": c, "folds": len(df)}
    for key, n, col in [("LS_post", "n", "auc_posterior_alpha_fit"),
                        ("LS_post_a0", "n", "auc_posterior"),
                        ("LS_prior", "n", "auc_cov_kappa_prior"),
                        ("LS_usgs", "n", "auc_usgs_prior"),
                        ("LQ_post", "n_lq", "auc_lq_posterior_alpha_fit"),
                        ("LQ_post_a0", "n_lq", "auc_lq_posterior"),
                        ("LQ_prior", "n_lq", "auc_lq_kappa_prior"),
                        ("LQ_usgs", "n_lq", "auc_lq_usgs_prior")]:
        v, nn, ne = wavg(df, n, col)
        r[key] = v
        r[key.split("_")[0] + "_rows"] = nn
        r[key.split("_")[0] + "_events"] = ne
    rows.append(r)

tab = pd.DataFrame(rows)
tab.to_csv(f"{OUT}/rq4/rq4_wavg_raw.csv", index=False, encoding="utf-8-sig")
pd.concat(per_event).to_csv(f"{OUT}/rq4/rq4_per_event_raw.csv", index=False, encoding="utf-8-sig")
with pd.option_context("display.width", 250, "display.max_columns", 30):
    print(tab.round(3).to_string(index=False))
    pe = pd.concat(per_event)
    for col in ["auc_posterior_alpha_fit", "auc_lq_posterior_alpha_fit"]:
        print("\n", col)
        print(pe.pivot(index="event", columns="cond", values=col)[[c for c in CONDS if c in set(pe.cond)]].round(3).to_string())
