"""후속실험 3(LOEO) 채점. 지시서 §4~§6.

results/loeo/*/eval_scores.csv 와 run_meta.json을 읽어
  - 조건별 LS AUC (prior q_LS / 사후 p_LS), 가중평균과 pooled
  - 회차별 kappa, b_LS, a_LS, 기존 loss, BCE 합
  - 지진 안 층화 부트스트랩 3,000회로 조건 간 차이의 95% 구간과 P(차이>0)
  - 판정 (지시서 §5 단계 5)
를 내고 results/loeo/LOEO_결과.xlsx 한 파일로 저장한다.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

OUT = Path("results/loeo")
XLSX = OUT / "LOEO_결과.xlsx"

# 지시서 §2-4. AUC가 정의되는 5개 지진과 시험 행 수(= 가중치).
EVENTS = ["2000 돗토리", "2004 니가타현주에쓰", "2016 구마모토", "2018 오사카", "2018 훗카이도"]
WEIGHTS = {"2000 돗토리": 24, "2004 니가타현주에쓰": 10, "2016 구마모토": 29,
           "2018 오사카": 7, "2018 훗카이도": 13}
W_SUM = sum(WEIGHTS.values())          # 83

N_BOOT, BOOT_SEED = 3000, 0
NA_TEXT = "AUC 정의 불가(음성 0)"

# 조건 정의. folds=None이면 1회 실행, 아니면 지진 하나씩 가린 5회차다.
CONDITIONS = [
    ("A0",      "A", "기존 prior, 산지 없음, omega=0 (기존 3번 재현)",        None),
    ("A1",      "A", "기존 prior + kappa·m, omega=0",                        None),
    ("A2",      "A", "기존 prior + kappa·m, omega=4.35 (교수님 제안)",        EVENTS),
    ("B0",      "B", "면적 항 prior, b=0 고정, omega=0 (면적 항 기준)",       None),
    ("B1",      "B", "면적 항 prior + kappa·m, omega=0",                      None),
    ("B2",      "B", "면적 항 prior + kappa·m, omega=4.35 (제안 + 면적 항)",   EVENTS),
    ("B2-w1",   "B", "(선택) B2의 omega=1 민감도",                            EVENTS),
    ("B2-w10",  "B", "(선택) B2의 omega=10 민감도",                           EVENTS),
    ("B0-log",  "B", "(추가) B0를 기존 브랜치의 log(pi) 링크로",               None),
    ("B2-log",  "B", "(추가) B2를 기존 브랜치의 log(pi) 링크로",               EVENTS),
]
COND_BY_ID = {c[0]: c for c in CONDITIONS}

# 지시서 §6 참고 기준값
REFERENCE = [
    ("USGS prior 단독", 0.797),
    ("산지 비율 단독", 0.806),
    ("면적 항 prior 단독", 0.840),
    ("면적 항 사후 (log 버전, 26.09.16 자료)", 0.855),
]


# ------------------------------------------------------------------ 읽기

def _run_dir(cond_id: str, event: str | None) -> Path:
    return OUT / cond_id if event is None else OUT / cond_id / event


def load_run(cond_id: str, event: str | None):
    """한 실행의 평가 점수표와 학습 결과를 읽는다."""
    d = _run_dir(cond_id, event)
    scores = pd.read_csv(d / "eval_scores.csv", dtype={"muni_code": str})
    meta = json.loads((d / "run_meta.json").read_text(encoding="utf-8"))
    return scores, meta


def held_out_scores(cond_id: str) -> pd.DataFrame:
    """채점에 쓸 LS 점수표를 만든다.

    1회 실행 조건  : 그 한 번의 결과에서 5개 지진 행을 전부 가져온다.
    5회차 조건     : 회차마다 '그 회차의 시험 지진' 행만 가져온다(정답을 안 본 예측).
    """
    folds = COND_BY_ID[cond_id][3]
    frames = []
    for event in (EVENTS if folds else [None]):
        scores, _ = load_run(cond_id, None if folds is None else event)
        rows = scores[scores["ls_eval_mask"].astype(bool)]
        rows = rows[rows["event"].isin(EVENTS if folds is None else [event])]
        frames.append(rows.assign(fold=event or "단일 실행"))
    out = pd.concat(frames, ignore_index=True)
    assert len(out) == W_SUM, f"{cond_id}: {len(out)}행 (83이어야 함)"
    return out


# ------------------------------------------------------------------ 지표

def auc_or_nan(y, s):
    y = np.asarray(y)
    if y.min() == y.max():
        return np.nan
    return float(roc_auc_score(y, s))


def weighted_auc(df: pd.DataFrame, score_col: str) -> float:
    """지진별 AUC를 시험 행 수로 가중평균한다. (§4의 24·10·29·7·13 ÷ 83)"""
    num = den = 0.0
    for event, g in df.groupby("event"):
        a = auc_or_nan(g["ls_true"], g[score_col])
        if np.isnan(a):
            continue
        num += a * WEIGHTS[event]
        den += WEIGHTS[event]
    return num / den


def per_event_auc(df: pd.DataFrame, score_col: str) -> dict[str, float]:
    return {e: auc_or_nan(g["ls_true"], g[score_col]) for e, g in df.groupby("event")}


def lq_summary(cond_id: str) -> tuple[float, float, str]:
    """LQ 사후 AUC. LQ 라벨은 가린 적이 없다.

    1회 실행 조건 : 그 실행의 LQ 가중/전체 AUC.
    5회차 조건    : 회차마다 낸 값의 평균(회차별 범위는 비고에 적는다).
    """
    folds = COND_BY_ID[cond_id][3]
    wavgs, pooleds = [], []
    for event in (EVENTS if folds else [None]):
        scores, _ = load_run(cond_id, None if folds is None else event)
        rows = scores[scores["lq_eval_mask"].astype(bool)]
        num = den = 0.0
        for _, g in rows.groupby("event"):
            a = auc_or_nan(g["lq_true"], g["p_lq_post"])
            if np.isnan(a):
                continue
            num += a * len(g)
            den += len(g)
        wavgs.append(num / den)
        pooleds.append(auc_or_nan(rows["lq_true"], rows["p_lq_post"]))
    if folds is None:
        return wavgs[0], pooleds[0], "1회 실행"
    return (float(np.mean(wavgs)), float(np.mean(pooleds)),
            f"5회차 평균 (회차 범위 {min(wavgs):.4f}~{max(wavgs):.4f})")


# ------------------------------------------------------------------ 부트스트랩

def bootstrap_draws(df: pd.DataFrame):
    """지진 안에서 양성과 음성을 따로 복원추출한 표본 3,000벌의 행 index.

    모든 조건이 같은 표본을 쓰므로 조건 간 차이가 짝지어진다(paired).
    지진별로 (양성 index [N_BOOT, n_pos], 음성 index [N_BOOT, n_neg])를 돌려준다.
    """
    rng = np.random.default_rng(BOOT_SEED)
    y, ev = df["ls_true"].to_numpy(), df["event"].to_numpy()
    draws = {}
    for event in EVENTS:
        pos = np.flatnonzero((ev == event) & (y == 1))
        neg = np.flatnonzero((ev == event) & (y == 0))
        draws[event] = (rng.choice(pos, size=(N_BOOT, len(pos)), replace=True),
                        rng.choice(neg, size=(N_BOOT, len(neg)), replace=True))
    return draws


def boot_weighted_auc_curve(scores: np.ndarray, draws) -> np.ndarray:
    """표본 3,000벌 각각의 가중 AUC [N_BOOT].

    AUC = P(양성 점수 > 음성 점수) + 0.5 P(같음)이라는 정의를 그대로 쓴다.
    표본마다 양성·음성 수가 같아서 통째로 벡터 연산으로 낼 수 있다.
    """
    num, den = np.zeros(N_BOOT), 0.0
    for event in EVENTS:
        pos_idx, neg_idx = draws[event]
        pos = scores[pos_idx][:, :, None]        # [N_BOOT, n_pos, 1]
        neg = scores[neg_idx][:, None, :]        # [N_BOOT, 1, n_neg]
        auc = ((pos > neg).sum(axis=(1, 2)) + 0.5 * (pos == neg).sum(axis=(1, 2))) / (
            pos.shape[1] * neg.shape[2])
        num += auc * WEIGHTS[event]
        den += WEIGHTS[event]
    return num / den


def aligned(df: pd.DataFrame) -> pd.DataFrame:
    """조건끼리 행을 맞추기 위해 (지진, 시정촌코드) 순으로 정렬한다."""
    return df.sort_values(["event", "muni_code"]).reset_index(drop=True)


def bootstrap_diff(base_curve, other_curve, base_df, other_df, score_col):
    """other − base의 가중 AUC 차이. 95% 구간과 '0보다 클 확률'."""
    diffs = other_curve - base_curve
    return {
        "차이(관측)": weighted_auc(other_df, score_col) - weighted_auc(base_df, score_col),
        "95% 하한": float(np.percentile(diffs, 2.5)),
        "95% 상한": float(np.percentile(diffs, 97.5)),
        "0보다 클 확률": float((diffs > 0).mean()),
    }


# ------------------------------------------------------------------ 판정

def verdict(cond_id: str, base_id: str, tables, boot_rows) -> str:
    """지시서 §5 단계 5."""
    post = tables[cond_id]["ls_post_wavg"]
    base = tables[base_id]["ls_post_wavg"]
    kappas = tables[cond_id]["kappas"]
    if not kappas:
        return "판정 대상 아님(단일 실행 기준선)"

    signs = {np.sign(k) for k in kappas}
    same_sign = len(signs) == 1 and 0 not in signs
    p = next(r["0보다 클 확률"] for r in boot_rows
             if r["비교"] == f"{cond_id} − {base_id}" and r["점수"] == "사후 p_LS")

    if post > base and p >= 0.95 and same_sign:
        return "성공"
    if post > base:
        reason = []
        if p < 0.95:
            reason.append(f"P={p:.3f} < 0.95")
        if not same_sign:
            reason.append("kappa 부호가 회차마다 다름")
        return "방향 확인 (" + ", ".join(reason) + ")" if reason else "성공"
    return f"실패 ({cond_id} {post:.4f} ≤ {base_id} {base:.4f})"


def round4(df: pd.DataFrame) -> pd.DataFrame:
    """지시서 §1. 숫자는 소수 넷째 자리까지만 남긴다. 문자열이 섞인 칸도 안전하게 처리한다."""
    out = df.copy()
    for col in out.columns:
        out[col] = out[col].map(lambda v: round(v, 4) if isinstance(v, (float, np.floating))
                                else v)
    return out


# ------------------------------------------------------------------ 실행기록

def run_log(fold_df: pd.DataFrame) -> pd.DataFrame:
    """지시서 §6 '실행기록' 시트. 재현에 필요한 사실만 적는다."""
    def git(*args):
        try:
            return subprocess.run(["git", *args], capture_output=True, text=True,
                                  check=True).stdout.strip()
        except Exception as exc:                      # git이 없거나 저장소 밖일 때
            return f"확인 불가 ({exc})"

    rows = [
        ("브랜치", git("rev-parse", "--abbrev-ref", "HEAD")),
        ("커밋 해시", git("rev-parse", "HEAD")),
        ("작업 트리 상태", git("status", "--porcelain") or "깨끗함(커밋되지 않은 변경 없음)"),
        ("실행 스크립트", "run_loeo.sh (학습 30회) -> score_loeo.py (채점)"),
        ("공통 설정", "3000 epoch / Adam lr 0.02 / weight_decay 0 / lam_gamma 10 / seed 0"),
        ("학습 행 수", "418행 (모든 조건 동일, 시험 지진의 피해 건수도 NLL에 포함)"),
        ("평가 행 수", "LS 125행 = 양성 105 / 음성 20. AUC 정의 지진 5개, 가중치 24·10·29·7·13 (합 83)"),
        ("산지 변수", "국세조사 mountain_ratio (통계 XLSX 헤더 4번째 줄). "
                    "loader.py가 학습 418행 기준으로 표준화한 z_mtn을 그대로 사용"),
        ("면적 자료", "USGS XLSX의 area_km2 (e-Stat B1101 총면적). 이벤트 시트별로 들어 있어 "
                    "합병 전후 면적이 자동 구분된다. 419행 전부 존재, 결측·0 이하 없음"),
        ("위도 처리", "시정촌별 위도 자료가 없어 현청 소재지 위도(schema.PREFECTURE_CAPITAL_LAT)를 사용. "
                    "지시서 §2-2가 허용한 '지진별 대표 위도'보다 한 단계 세밀하다. "
                    "같은 현 안에서는 칸 넓이가 상수라 지진 안 순위에는 영향이 없다"),
        ("칸 넓이 식", "기존 면적 항 브랜치(followup3-area-avg-*)의 계산을 그대로 옮겼다. "
                     "cell = (arcsec/3600 × 111.32 × cos(위도)) × (arcsec/3600 × 110.95). "
                     "지시서 §2-2의 0.23160² × cos(위도)와는 0.1% 미만 차이"),
        ("k 확인값", "구마모토시(熊本市) 43100: 칸 0.045065 km², k = 8,661 (지시서 확인값 약 8,653). "
                   "아쓰마초(厚真町) 01581: 칸 0.039167 km², k = 10,330 (지시서 확인값 약 10,330)"),
        ("c 적용 범위", "기존 브랜치와 같이 log k를 LS(7.5″)와 LQ(15″) 양쪽에 c=1로 넣는다. "
                     "지시서 §2-1 B의 LQ 식도 같다"),
        ("링크 함수", "주 조건은 지시서 §2-1 B 그대로 logit(pi) + log k. "
                    "기존 브랜치는 log(pi) + log k였고, 이것도 B0-log / B2-log로 함께 돌렸다"),
        ("BCE 구현", "F.binary_cross_entropy_with_logits(z_LS[대상], y, reduction='sum'), "
                   "확률은 사후가 아니라 prior q_LS = sigmoid(z_LS)"),
        ("기존 loss", "손대지 않았다. loss = NLL(418행 합) + 10·(Σγ_LS² + Σγ_LQ²). 행 수로 나누지 않는다"),
        ("옵션 끈 상태 확인", "모든 새 옵션을 기본값으로 두고 돌린 A0의 predictions.csv / params.csv가 "
                        "코드 수정 전 결과와 완전히 같다(diff 무차이)"),
        ("kappa optimizer 포함", "--mtn-prior를 켠 모든 실행에서 True로 출력되고, 아니면 RuntimeError로 멈춘다"),
        ("NaN / 발산", "30회 실행 전부 loss_history에 NaN·Inf 없음, 최종 loss < 초기 loss"),
        ("부트스트랩", f"{N_BOOT}회, seed {BOOT_SEED}. 지진 안에서 양성·음성을 따로 복원추출하고 "
                    "모든 조건이 같은 표본을 써서 짝지어 비교한다"),
        ("총 실행 수", f"{len(fold_df)}회 (필수 14 + 선택 10 + 링크 민감도 6)"),
    ]
    log = pd.DataFrame(rows, columns=["항목", "내용"])

    # 지시서 §6: 빈칸을 두지 않는다.
    log["학습 파라미터 수"] = "해당 없음(설명 행)"
    log["실행 명령"] = "해당 없음(설명 행)"

    cmds = fold_df[["조건", "시험 지진", "학습 파라미터 수", "실행 명령"]].copy()
    cmds.columns = ["항목", "내용", "학습 파라미터 수", "실행 명령"]
    cmds["항목"] = "실행 " + cmds["항목"]
    cmds["내용"] = "시험 지진: " + cmds["내용"].astype(str)
    return pd.concat([log, cmds], ignore_index=True)


# ------------------------------------------------------------------ 본체

def main():
    tables, fold_rows = {}, []

    for cond_id, family, note, folds in CONDITIONS:
        df = held_out_scores(cond_id)
        lq_w, lq_p, lq_note = lq_summary(cond_id)
        tables[cond_id] = {
            "family": family, "note": note, "folds": folds, "scores": df,
            "ls_post_wavg": weighted_auc(df, "p_ls_post"),
            "ls_post_pooled": auc_or_nan(df["ls_true"], df["p_ls_post"]),
            "ls_prior_wavg": weighted_auc(df, "q_ls_prior"),
            "ls_prior_pooled": auc_or_nan(df["ls_true"], df["q_ls_prior"]),
            "ls_usgs_wavg": weighted_auc(df, "pi_ls_usgs"),
            "mse_ls": float(((df["p_ls_post"] - df["ls_true"]) ** 2).mean()),
            "lq_post_wavg": lq_w, "lq_post_pooled": lq_p, "lq_note": lq_note,
            "kappas": [],
        }

        for event in (folds if folds else [None]):
            scores, meta = load_run(cond_id, event)
            test = event or "전체(가린 지진 없음)"
            rows = df[df["fold"] == (event or "단일 실행")]
            kappa = meta["kappa"]
            if kappa != "":
                tables[cond_id]["kappas"].append(float(kappa))
            fold_rows.append({
                "조건": cond_id, "회차": (EVENTS.index(event) + 1) if event else 1,
                "시험 지진": test,
                "시험 행 n": len(rows),
                "시험 양성": int(rows["ls_true"].sum()),
                "시험 음성": int((rows["ls_true"] == 0).sum()),
                "BCE 대상 행": meta["n_bce_rows"] if meta["omega"] else "0 (BCE 미사용)",
                "omega": meta["omega"],
                "시험 AUC prior q_LS": auc_or_nan(rows["ls_true"], rows["q_ls_prior"]),
                "시험 AUC 사후 p_LS": auc_or_nan(rows["ls_true"], rows["p_ls_post"]),
                "kappa": float(kappa) if kappa != "" else "산지 항 없음",
                "e^kappa": float(np.exp(float(kappa))) if kappa != "" else "산지 항 없음",
                "b_LS": meta["b_ls"],
                "a_LS": meta["a_ls"] if meta["a_ls"] != "" else "B 계열: a=1 고정",
                "기존 loss (NLL+패널티)": meta["loss_base_final"],
                "BCE 합": meta["bce_sum_final"],
                "학습 파라미터 수": meta["n_params"],
                "실행 명령": meta["argv"],
            })

    # ---- 부트스트랩 ----
    # 모든 조건의 83행이 (지진, 시정촌코드) 기준으로 같은 행인지 확인하고 표본을 공유한다.
    ref = aligned(tables["A0"]["scores"])
    for cid, t in tables.items():
        t["aligned"] = aligned(t["scores"])
        assert (t["aligned"]["muni_code"].to_numpy() == ref["muni_code"].to_numpy()).all(), cid
        assert (t["aligned"]["ls_true"].to_numpy() == ref["ls_true"].to_numpy()).all(), cid

    draws = bootstrap_draws(ref)
    curves = {(cid, col): boot_weighted_auc_curve(t["aligned"][col].to_numpy(), draws)
              for cid, t in tables.items()
              for col in ("p_ls_post", "q_ls_prior")}

    comparisons = [("A2", "A0"), ("A2", "A1"), ("B2", "B0"), ("B2", "B1"), ("B2", "A2"),
                   ("B2-w1", "B0"), ("B2-w10", "B0"), ("B2-log", "B0-log")]
    boot_rows = []
    for other, base in comparisons:
        for label, col in (("사후 p_LS", "p_ls_post"), ("prior q_LS", "q_ls_prior")):
            r = bootstrap_diff(curves[(base, col)], curves[(other, col)],
                               tables[base]["scores"], tables[other]["scores"], col)
            boot_rows.append({"비교": f"{other} − {base}", "점수": label,
                              "부트스트랩 횟수": N_BOOT, "seed": BOOT_SEED, **r})

    verdicts = {
        "A2": verdict("A2", "A0", tables, boot_rows),
        "B2": verdict("B2", "B0", tables, boot_rows),
        "B2-w1": verdict("B2-w1", "B0", tables, boot_rows),
        "B2-w10": verdict("B2-w10", "B0", tables, boot_rows),
        "B2-log": verdict("B2-log", "B0-log", tables, boot_rows),
    }

    # ---- 시트 ----
    summary = pd.DataFrame([{
        "조건": cid, "계열": t["family"], "설명": t["note"],
        "실행 수": 5 if t["folds"] else 1,
        "LS 사후 가중": t["ls_post_wavg"], "LS 사후 전체": t["ls_post_pooled"],
        "LS prior(q_LS) 가중": t["ls_prior_wavg"], "LS prior(q_LS) 전체": t["ls_prior_pooled"],
        "LS USGS pi 가중(참고)": t["ls_usgs_wavg"],
        "LS MSE (시험 83행)": t["mse_ls"],
        "LQ 사후 가중": t["lq_post_wavg"], "LQ 사후 전체": t["lq_post_pooled"],
        "LQ 비고": t["lq_note"],
        "kappa 부호": ("모두 " + ("+" if t["kappas"][0] > 0 else "−")
                       if t["kappas"] and len({np.sign(k) for k in t["kappas"]}) == 1
                       else ("회차마다 다름" if t["kappas"] else "산지 항 없음")),
        "판정": verdicts.get(cid, "기준선(판정 대상 아님)"),
    } for cid, t in tables.items()])

    # 지시서 §6: 참고 기준값을 요약 시트 아래에 함께 적는다.
    blank = {c: "해당 없음" for c in summary.columns}
    tail = [{**blank, "조건": "── 참고 기준값 (지시서 §6) ──", "설명": "아래 네 줄은 비교용 기준값이다"}]
    for name, value in REFERENCE:
        tail.append({**blank, "조건": "참고", "설명": name, "LS 사후 가중": value,
                     "판정": "지시서 §6 기준값"})
    summary = pd.concat([summary, pd.DataFrame(tail)], ignore_index=True)

    fold_df = pd.DataFrame(fold_rows)

    ev_rows = []
    for event in EVENTS:
        pos = int(tables["A0"]["scores"].query("event == @event")["ls_true"].sum())
        for cid, t in tables.items():
            g = t["scores"][t["scores"]["event"] == event]
            ev_rows.append({
                "지진": event, "조건": cid,
                "행 n": len(g), "양성": pos, "음성": len(g) - pos,
                "AUC prior q_LS": auc_or_nan(g["ls_true"], g["q_ls_prior"]),
                "AUC 사후 p_LS": auc_or_nan(g["ls_true"], g["p_ls_post"]),
            })
    event_df = pd.DataFrame(ev_rows)

    boot_df = pd.DataFrame(boot_rows)

    repro = pd.DataFrame([
        {"항목": "A0 LS 사후 가중", "재현값": tables["A0"]["ls_post_wavg"],
         "기준값": 0.7222, "차이": tables["A0"]["ls_post_wavg"] - 0.7222,
         "출처": "지시서 §5 단계 1-6 (기존 3번)"},
        {"항목": "A0 LS prior(USGS pi) 가중", "재현값": tables["A0"]["ls_usgs_wavg"],
         "기준값": 0.7969, "차이": tables["A0"]["ls_usgs_wavg"] - 0.7969,
         "출처": "지시서 §5 단계 1-6"},
        {"항목": "A1 LS 사후 가중", "재현값": tables["A1"]["ls_post_wavg"],
         "기준값": 0.717, "차이": tables["A1"]["ls_post_wavg"] - 0.717,
         "출처": "지시서 §4 A1 비고 (발표자료 12쪽 ③)"},
        {"항목": "A1 kappa", "재현값": tables["A1"]["kappas"][0],
         "기준값": 0.05, "차이": tables["A1"]["kappas"][0] - 0.05,
         "출처": "지시서 §4 A1 비고"},
        {"항목": "B0 LS prior(q_LS) 가중", "재현값": tables["B0"]["ls_prior_wavg"],
         "기준값": 0.840, "차이": tables["B0"]["ls_prior_wavg"] - 0.840,
         "출처": "지시서 §6 참고 기준값 '면적 항 prior 단독'"},
        {"항목": "B0 LS 사후 가중", "재현값": tables["B0"]["ls_post_wavg"],
         "기준값": 0.855, "차이": tables["B0"]["ls_post_wavg"] - 0.855,
         "출처": "지시서 §6 참고 기준값 '면적 항 사후'"},
        {"항목": "B0-log LS 사후 가중", "재현값": tables["B0-log"]["ls_post_wavg"],
         "기준값": 0.855, "차이": tables["B0-log"]["ls_post_wavg"] - 0.855,
         "출처": "같은 기준값을 기존 브랜치 링크(log)로"},
    ])

    ref_df = pd.DataFrame(REFERENCE, columns=["참고 기준", "LS 가중 AUC"])

    sheets = {"요약": summary, "회차별": fold_df, "이벤트별": event_df,
              "부트스트랩": boot_df, "재현": repro, "참고기준값": ref_df,
              "실행기록": run_log(fold_df)}

    # 지시서 §1: 모든 숫자는 소수 넷째 자리까지 기록한다.
    sheets = {name: round4(df) for name, df in sheets.items()}

    for name, df in sheets.items():
        df.to_csv(OUT / f"sheet_{name}.csv", index=False, encoding="utf-8-sig")

    with pd.ExcelWriter(XLSX, engine="openpyxl") as xw:
        for name, df in sheets.items():
            df.to_excel(xw, sheet_name=name, index=False)
    print(f"저장: {XLSX}")

    return {**sheets, "_tables": tables, "_verdicts": verdicts}


if __name__ == "__main__":
    r = main()
    pd.set_option("display.width", 250)
    print(r["요약"].round(4).to_string(index=False))
    print()
    print(r["부트스트랩"].round(4).to_string(index=False))
    print()
    print(r["재현"].round(4).to_string(index=False))
