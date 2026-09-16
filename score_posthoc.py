"""사후 탐색(C 계열) 채점. 지시서 §4 조건표 밖이고 §5 판정 대상이 아니다.

b_LQ 고정을 푼 것이 무엇을 바꾸는지 B 계열과 나란히 본다.
"""
from __future__ import annotations
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

EVENTS = ["2000 돗토리", "2004 니가타현주에쓰", "2016 구마모토", "2018 오사카", "2018 훗카이도"]
W_LS = {"2000 돗토리": 24, "2004 니가타현주에쓰": 10, "2016 구마모토": 29,
        "2018 오사카": 7, "2018 훗카이도": 13}
LQ_EVENTS = {"2000 돗토리": 8, "2004 니가타현주에쓰": 23, "2016 구마모토": 40,
             "2018 훗카이도": 40, "2021 후쿠시마": 7, "2024 노토반도": 64}
N_BOOT, SEED = 3000, 0

# (표시이름, 폴더, 5회차 여부)
CONDS = [("B0  (b_LQ=0 고정)", "results/loeo/B0", False),
         ("C0  (b_LQ 학습)",   "results/posthoc/C0", False),
         ("B2  (b_LQ=0 고정)", "results/loeo/B2", True),
         ("C2  (b_LQ 학습)",   "results/posthoc/C2", True)]


def runs(path, folds):
    out = []
    for e in (EVENTS if folds else [None]):
        d = Path(path) / (e if e else "")
        out.append((pd.read_csv(d / "eval_scores.csv", dtype={"muni_code": str}),
                    json.loads((d / "run_meta.json").read_text(encoding="utf-8")), e))
    return out


def ls_heldout(path, folds):
    """LS는 5회차 조건이면 그 회차의 시험 지진 행만 모은다."""
    fr = []
    for sc, _, e in runs(path, folds):
        r = sc[sc.ls_eval_mask.astype(bool)]
        fr.append(r[r.event.isin(EVENTS if not folds else [e])])
    return pd.concat(fr, ignore_index=True)


def wauc(df, true_col, score_col, weights):
    n = d = 0.0
    for e, w in weights.items():
        g = df[df.event == e]
        if len(g) == 0 or g[true_col].min() == g[true_col].max():
            continue
        n += roc_auc_score(g[true_col], g[score_col]) * w
        d += w
    return n / d


def draws(df, true_col, weights):
    rng = np.random.default_rng(SEED)
    out = {}
    for e in weights:
        s = df.index[df.event == e]
        y = df.loc[s, true_col].to_numpy()
        pos, neg = s[y == 1].to_numpy(), s[y == 0].to_numpy()
        if len(pos) == 0 or len(neg) == 0:
            continue
        out[e] = (rng.choice(pos, (N_BOOT, len(pos))), rng.choice(neg, (N_BOOT, len(neg))))
    return out


def curve(score, dw, weights):
    n, d = np.zeros(N_BOOT), 0.0
    for e, (pi, ni) in dw.items():
        P, N = score[pi][:, :, None], score[ni][:, None, :]
        n += (((P > N).sum(axis=(1, 2)) + 0.5 * (P == N).sum(axis=(1, 2)))
              / (P.shape[1] * N.shape[2])) * weights[e]
        d += weights[e]
    return n / d


def bce(y, q):
    q = np.clip(q, 1e-12, 1 - 1e-12)
    return float(-(y * np.log(q) + (1 - y) * np.log(1 - q)).mean())


rows = []
for name, path, folds in CONDS:
    ls = ls_heldout(path, folds)
    lq = [sc[sc.lq_eval_mask.astype(bool)] for sc, _, _ in runs(path, folds)]
    metas = [m for _, m, _ in runs(path, folds)]
    rows.append({
        "조건": name,
        "LS 사후 가중": wauc(ls, "ls_true", "p_ls_post", W_LS),
        "LS MSE": float(((ls.p_ls_post - ls.ls_true) ** 2).mean()),
        "LQ 사후 가중": np.mean([wauc(d, "lq_true", "p_lq_post", LQ_EVENTS) for d in lq]),
        "LQ prior 가중": np.mean([wauc(d, "lq_true", "q_lq_prior", LQ_EVENTS) for d in lq]),
        "LQ MSE(사후)": np.mean([float(((d.p_lq_post - d.lq_true) ** 2).mean()) for d in lq]),
        "LQ MSE(prior)": np.mean([float(((d.q_lq_prior - d.lq_true) ** 2).mean()) for d in lq]),
        "LQ BCE(prior)": np.mean([bce(d.lq_true.to_numpy(), d.q_lq_prior.to_numpy()) for d in lq]),
        "q_LQ 중앙값": np.mean([float(d.q_lq_prior.median()) for d in lq]),
        "b_LQ": np.mean([float(m.get("b_lq") or 0.0) for m in metas]),
        "b_LS": np.mean([float(m["b_ls"]) for m in metas]),
        "kappa": (np.mean([float(m["kappa"]) for m in metas]) if metas[0]["kappa"] != ""
                  else "산지 항 없음"),
    })
summary = pd.DataFrame(rows)

# 부트스트랩: LQ는 라벨을 가린 적이 없어 조건 간 행이 같다.
lq_ref = [sc[sc.lq_eval_mask.astype(bool)].reset_index(drop=True)
          for sc, _, _ in runs("results/loeo/B0", False)][0]
dw = draws(lq_ref, "lq_true", LQ_EVENTS)
def lq_score(path, folds):
    ds = [sc[sc.lq_eval_mask.astype(bool)].reset_index(drop=True) for sc, _, _ in runs(path, folds)]
    return np.mean([d.p_lq_post.to_numpy() for d in ds], axis=0)
boot = []
for a, b in [("C0  (b_LQ 학습)", "B0  (b_LQ=0 고정)"), ("C2  (b_LQ 학습)", "B2  (b_LQ=0 고정)")]:
    pa = dict((n, (p, f)) for n, p, f in CONDS)
    d = curve(lq_score(*pa[a]), dw, LQ_EVENTS) - curve(lq_score(*pa[b]), dw, LQ_EVENTS)
    boot.append({"비교": f"{a.split()[0]} − {b.split()[0]}", "지표": "LQ 사후 가중 AUC",
                 "차이": float(d.mean()), "95% 하한": float(np.percentile(d, 2.5)),
                 "95% 상한": float(np.percentile(d, 97.5)), "0보다 클 확률": float((d > 0).mean())})
boot = pd.DataFrame(boot)

Path("results/posthoc").mkdir(parents=True, exist_ok=True)
with pd.ExcelWriter("results/posthoc/사후탐색_결과.xlsx", engine="openpyxl") as xw:
    summary.round(4).to_excel(xw, sheet_name="요약", index=False)
    boot.round(4).to_excel(xw, sheet_name="부트스트랩", index=False)
pd.set_option("display.width", 250)
print(summary.round(4).to_string(index=False))
print()
print(boot.round(4).to_string(index=False))
