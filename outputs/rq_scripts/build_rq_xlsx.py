"""AdminDER RQ1~5 정리 엑셀. 지금은 RQ1만 채운다 (RQ2~5는 시트만).

숫자 출처
- AdminDER ①: outputs/holdout_summary_rq4nl_full_* (9개 지진 LOEO, 8개 학습)
- AdminDER ②: outputs/holdout_summary_rq4d5_full_* (DPM 5개 지진 안 LOEO, 4개 학습)
- USGS 평균집계: 같은 CSV의 auc_usgs_prior / auc_lq_usgs_prior
- USGS 액상화 최대집계: raw/재난프로젝트_시정촌별_USGS.xlsx의 LQ_prior(최대)로 직접 계산 (평가 시정촌 = AdminDER와 동일)
- DisasterNet: 선배 문서(Desktop/DisasterNet 시정촌 실험.html, 칸 단위 실험.html, 2026-10-23), seed 5개 평균
실행: python build_rq_xlsx.py <출력 xlsx>
"""
import glob
import sys

import numpy as np
import pandas as pd
from openpyxl import Workbook
from openpyxl.comments import Comment
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

REPO = r"C:\Users\PC\Desktop\pilotA"
OUT = sys.argv[1]
DPM5 = ["2016 구마모토", "2018 오사카", "2018 훗카이도", "2021 후쿠시마", "2024 노토반도"]
ORDER = ["2000 돗토리", "2004 니가타현주에쓰", "2007 니가타현주에쓰오키", "2008 이와테미야기",
         "2016 구마모토", "2018 오사카", "2018 훗카이도", "2021 후쿠시마", "2024 노토반도"]


def summary(tag):
    df = pd.concat([pd.read_csv(f) for f in glob.glob(f"{REPO}/outputs/holdout_summary_{tag}_*.csv")])
    return df.set_index("event")


def auc(s, y):
    s, y = np.asarray(s, float), np.asarray(y)
    p, n = s[y == 1], s[y == 0]
    if len(p) == 0 or len(n) == 0:
        return np.nan
    d = p[:, None] - n[None, :]
    return float(((d > 0).sum() + 0.5 * (d == 0).sum()) / d.size)


S1, S2 = summary("rq4nl_full"), summary("rq4d5_full")
# 액상화 라벨도 학습에 쓴 판 (교수님 요청 2026-11-13). ① = 10월 lqJ, ② = rq1_lqlabels_dpm5.py로 새로 돌림
S1L, S2L = summary("lqJ"), summary("rq1d5lql_full")
_old = pd.concat([pd.read_csv(f) for f in glob.glob(f"{REPO}/outputs/rq4/_폐기_LQ라벨켠판/holdout_files/holdout_summary_rq4_full_*.csv")]).set_index("event")
for _c in ("auc_posterior_alpha_fit", "auc_lq_posterior_alpha_fit"):  # 10월 lqJ = 11월 다시 돌린 LQ 라벨판
    assert np.allclose(S1L[_c], _old.loc[S1L.index, _c], equal_nan=True), _c
    assert (S1L[_c].isna() == S1.loc[S1L.index, _c].isna()).all() and (S2L[_c].isna() == S2.loc[S2L.index, _c].isna()).all()
assert len(S1L) == 9 and len(S2L) == 5
det = pd.concat([pd.read_csv(f) for f in glob.glob(f"{REPO}/outputs/holdout_detail_lq_rq4nl_full_*.csv")])
LQMAX = {}
for ev, g in det.groupby("event"):
    u = pd.read_excel(f"{REPO}/raw/재난프로젝트_시정촌별_USGS.xlsx", ev, header=3)
    u = u[pd.to_numeric(u["시정촌코드"], errors="coerce").notna()].copy()
    u["code"] = u["시정촌코드"].astype(int)
    m = g.merge(u[["code", "LQ_prior(평균)", "LQ_prior(최대)"]], left_on="muni_code", right_on="code", how="left")
    assert m["LQ_prior(최대)"].notna().all() and np.allclose(m["LQ_prior(평균)"], m.pi_lq), ev
    LQMAX[ev] = auc(m["LQ_prior(최대)"], m.lq_true)
det_ls = pd.concat([pd.read_csv(f) for f in glob.glob(f"{REPO}/outputs/holdout_detail_rq4nl_full_*.csv")])
LSMAX = {}
for ev, g in det_ls.groupby("event"):
    u = pd.read_excel(f"{REPO}/raw/재난프로젝트_시정촌별_USGS.xlsx", ev, header=3)
    u = u[pd.to_numeric(u["시정촌코드"], errors="coerce").notna()].copy()
    u["code"] = u["시정촌코드"].astype(int)
    m = g.merge(u[["code", "LS_prior(평균)", "LS_prior(최대)"]], left_on="muni_code", right_on="code", how="left")
    assert m["LS_prior(최대)"].notna().all() and np.allclose(m["LS_prior(평균)"], m.pi_ls), ev
    LSMAX[ev] = auc(m["LS_prior(최대)"], m.ls_true)
MAX = {"LS": LSMAX, "LQ": LQMAX}

# DisasterNet: 언니 예측 파일(seed 0~4)을 AdminDER 평가 시정촌으로 채점한 결과 (score_dn.py → outputs/rq1/)
DNEV = pd.read_csv(f"{REPO}/outputs/rq1/dn_auc_by_event.csv")
DNW = pd.read_csv(f"{REPO}/outputs/rq1/dn_auc_weighted.csv")
DN_ORDER = list(dict.fromkeys(zip(DNEV.단위, DNEV.변형)))

COL = {"LS": ("n", "n_pos", "n_neg", "auc_usgs_prior", "auc_posterior_alpha_fit"),
       "LQ": ("n_lq", "n_pos_lq", "n_neg_lq", "auc_lq_usgs_prior", "auc_lq_posterior_alpha_fit")}
# 변환 prior = log p̄ + log k (USGS 평균을 시정촌 면적으로 바꾼 것, 학습 없음, cov·κ 없음). train.py report_holdout의 z_a / z_a_lq
TP = {"LS": "auc_A_own_prior", "LQ": "auc_lq_A_own_prior"}
for _h, _c in TP.items():  # 학습과 무관해야 하므로 ①·②·라벨판에서 값이 같아야 함
    assert np.allclose(S1.loc[S2.index, _c], S2[_c], equal_nan=True), _c
    assert np.allclose(S1[_c], S1L.loc[S1.index, _c], equal_nan=True), _c
    assert (S1[_c].isna() == S1[COL[_h][4]].isna()).all(), _c
HZ = {"LS": "산사태", "LQ": "액상화"}

# ---------- 스타일 ----------
F = "맑은 고딕"
f_title = Font(name=F, size=14, bold=True, color="2A2540")
f_h2 = Font(name=F, size=11, bold=True, color="2A2540")
f_head = Font(name=F, size=10, bold=True, color="FFFFFF")
f_body = Font(name=F, size=10, color="222222")
f_bold = Font(name=F, size=10, bold=True, color="222222")
f_note = Font(name=F, size=9, color="555555")
fill_head = PatternFill("solid", fgColor="6F5FB0")
fill_trace = PatternFill("solid", fgColor="EDE8FA")
fill_avg = PatternFill("solid", fgColor="F3F3F3")
fill_q = PatternFill("solid", fgColor="FFF4E5")
thin = Side(style="thin", color="C8C8D0")
box = Border(left=thin, right=thin, top=thin, bottom=thin)
center = Alignment(horizontal="center", vertical="center", wrap_text=True)
left = Alignment(horizontal="left", vertical="center", wrap_text=True)
NUM = "0.000"


def put(ws, r, c, v, font=f_body, fill=None, fmt=None, align=center, border=True):
    cell = ws.cell(row=r, column=c, value=v)
    cell.font, cell.alignment = font, align
    if fill:
        cell.fill = fill
    if fmt:
        cell.number_format = fmt
    if border:
        cell.border = box
    return cell


def header(ws, r, labels, c0=1):
    for i, h in enumerate(labels):
        put(ws, r, c0 + i, h, font=f_head, fill=fill_head)
    ws.row_dimensions[r].height = 42


def text(ws, r, v, font=f_body, span=13):
    ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=span)
    c = ws.cell(row=r, column=1, value=v)
    c.font, c.alignment = font, left
    return c


wb = Workbook()
ws = wb.active
ws.title = "RQ1"
for t in ("RQ2", "RQ3", "RQ4", "RQ5"):
    wb.create_sheet(t)

# ---------- RQ1 ----------
r = 1
text(ws, r, "RQ1. AdminDER는 학습하지 않은 새 지진에서 후속 재난 발생을 얼마나 정확히 추정하는가?", f_title)
ws.row_dimensions[r].height = 26
r += 1
for line in [
    "논문: AdminDER: Inferring Earthquake-Induced Cascading Hazards from Web-Published Administrative Damage Statistics (모델 이름 TRACE → AdminDER로 변경).",
    "평가: LOEO(지진 하나를 학습에서 빼고 그 지진으로 평가). 지표: 지진 안 AUC, 양성·음성이 둘 다 있는 지진만, 평가 시정촌 수로 가중평균.",
    "AdminDER 최종 설정: 산사태 E3(라벨 학습 + 분리), 액상화 J(분리, 라벨 미사용). λ_γ = λ_κ = 10, 3000 에폭. 새 지진의 α_e 하나만 그 지진 피해 건수로 맞춘 사후확률로 채점.",
    "변환 prior: USGS 평균집계 값 p̄를 시정촌 면적(칸 개수 k)으로 바꾼 log p̄ + log k. 학습 없음, 판독 범위(cov)·산지 비율(κ)·피해 통계 모두 안 씀. 산사태·액상화 같은 식.",
    "'AdminDER + 액상화 라벨 학습': 위 설정에서 학습 지진의 액상화 라벨도 학습에 쓴 것(나머지 동일). 평가 지진 라벨은 어느 쪽도 쓰지 않음.",
    "AdminDER는 결정적 모델(초기값 상수, 전체 배치)이라 1회 실행값. DisasterNet은 seed 0~4 다섯 번 평균.",
]:
    text(ws, r, line, f_note)
    ws.row_dimensions[r].height = 30
    r += 1

# 표 1: DPM 5개 지진 (DisasterNet과 비교 가능한 범위)
r += 1
text(ws, r, "표 1. DPM 있는 5개 지진 — USGS vs AdminDER vs DisasterNet 전 변형 (평가 시정촌 산사태 49곳 · 액상화 151곳, 모든 방법 동일)", f_h2, span=13)
r += 1
# 열: A 구분, B 방법, C~E 산사태 지진 3, F 산사태 가중, G~J 액상화 지진 4, K 액상화 가중, L·M seed별 가중 범위
EVC = {"LS": [e for e in DPM5 if pd.notna(S1.loc[e, COL["LS"][4]])],
       "LQ": [e for e in DPM5 if pd.notna(S1.loc[e, COL["LQ"][4]])]}
assert EVC["LS"] == ["2016 구마모토", "2018 오사카", "2018 훗카이도"]
assert EVC["LQ"] == ["2016 구마모토", "2018 훗카이도", "2021 후쿠시마", "2024 노토반도"]
CPOS = {("LS", e): 3 + i for i, e in enumerate(EVC["LS"])}
CPOS.update({("LQ", e): 7 + i for i, e in enumerate(EVC["LQ"])})
WPOS = {"LS": 6, "LQ": 11}
labels = ["구분", "방법"] + [f"산사태\n{e}" for e in EVC["LS"]] + ["산사태\n가중평균"] \
    + [f"액상화\n{e}" for e in EVC["LQ"]] + ["액상화\n가중평균", "산사태 가중\nseed별 범위", "액상화 가중\nseed별 범위"]
header(ws, r, labels)
r += 1
# 평가 시정촌 수 행 (가중평균 수식이 이 행을 쓴다)
nrow = r
put(ws, r, 1, "", fill=fill_avg); put(ws, r, 2, "평가 시정촌 수", font=f_bold, fill=fill_avg, align=left)
for (hz, ev), c in CPOS.items():
    put(ws, r, c, int(S1.loc[ev, COL[hz][0]]), font=f_bold, fill=fill_avg)
for hz, c in WPOS.items():
    a, b = get_column_letter(min(v for (h, _), v in CPOS.items() if h == hz)), get_column_letter(c - 1)
    put(ws, r, c, f"=SUM({a}{r}:{b}{r})", font=f_bold, fill=fill_avg)
put(ws, r, 12, "", fill=fill_avg); put(ws, r, 13, "", fill=fill_avg)
r += 1
put(ws, r, 1, "", fill=fill_avg); put(ws, r, 2, "양성 / 음성", font=f_body, fill=fill_avg, align=left)
for (hz, ev), c in CPOS.items():
    put(ws, r, c, f"{int(S1.loc[ev, COL[hz][1]])} / {int(S1.loc[ev, COL[hz][2]])}", fill=fill_avg)
for hz, c in WPOS.items():
    evs = EVC[hz]
    put(ws, r, c, f"{sum(int(S1.loc[e, COL[hz][1]]) for e in evs)} / {sum(int(S1.loc[e, COL[hz][2]]) for e in evs)}",
        fill=fill_avg)
put(ws, r, 12, "", fill=fill_avg); put(ws, r, 13, "", fill=fill_avg)
r += 1


ROWS = {}


def method_row(r, group, name, vals, fill=None, bold=False, rng=("–", "–")):
    """vals: {(재해, 지진): AUC 원값}. 가중평균은 수식."""
    ROWS[(group, name)] = r
    font = f_bold if bold else f_body
    put(ws, r, 1, group, fill=fill, align=left); put(ws, r, 2, name, fill=fill, font=font, align=left)
    for key, c in CPOS.items():
        put(ws, r, c, vals[key], fmt=NUM, fill=fill, font=font)
    for hz, c in WPOS.items():
        cols = [v for (h, _), v in CPOS.items() if h == hz]
        a, b = get_column_letter(min(cols)), get_column_letter(max(cols))
        put(ws, r, c, f"=SUMPRODUCT(${a}${nrow}:${b}${nrow},{a}{r}:{b}{r})/SUM(${a}${nrow}:${b}${nrow})",
            fmt=NUM, fill=fill or fill_avg, font=f_bold)
    put(ws, r, 12, rng[0], fill=fill); put(ws, r, 13, rng[1], fill=fill)


method_row(r, "USGS prior", "평균집계", {(h, e): float(S1.loc[e, COL[h][3]]) for (h, e) in CPOS}); r += 1
method_row(r, "USGS prior", "최대집계", {(h, e): MAX[h][e] for (h, e) in CPOS}); r += 1
method_row(r, "변환 prior", "log p̄ + log k (학습 없음)", {(h, e): float(S1.loc[e, TP[h]]) for (h, e) in CPOS}); r += 1
method_row(r, "AdminDER", "① 8개 지진 학습 (9개 LOEO)", {(h, e): float(S1.loc[e, COL[h][4]]) for (h, e) in CPOS},
           fill=fill_trace, bold=True); r += 1
method_row(r, "AdminDER", "② DPM 4개 지진 학습 (5개 LOEO)", {(h, e): float(S2.loc[e, COL[h][4]]) for (h, e) in CPOS},
           fill=fill_trace, bold=True); r += 1
method_row(r, "AdminDER + 액상화 라벨 학습", "① 8개 지진 학습 (9개 LOEO)",
           {(h, e): float(S1L.loc[e, COL[h][4]]) for (h, e) in CPOS}, fill=fill_trace); r += 1
method_row(r, "AdminDER + 액상화 라벨 학습", "② DPM 4개 지진 학습 (5개 LOEO)",
           {(h, e): float(S2L.loc[e, COL[h][4]]) for (h, e) in CPOS}, fill=fill_trace); r += 1
for unit, name in DN_ORDER:
    g = DNEV[(DNEV.단위 == unit) & (DNEV.변형 == name)]
    vals = {(h, e): float(g[(g.재해 == h) & (g.지진 == e)]["mean"].iloc[0]) for (h, e) in CPOS}
    for (h, e) in CPOS:  # 평가 시정촌 수가 AdminDER와 같아야 함
        assert int(g[(g.재해 == h) & (g.지진 == e)].평가시정촌.iloc[0]) == int(S1.loc[e, COL[h][0]]), (unit, name, h, e)
    wr = DNW[(DNW.단위 == unit) & (DNW.변형 == name)].set_index("재해")
    rng = tuple(f"{wr.loc[h, 'seed별_최소']:.3f} ~ {wr.loc[h, 'seed별_최대']:.3f}" for h in ("LS", "LQ"))
    label = name + (" (확인 실험)" if "같은분산" in name else "")
    method_row(r, f"DisasterNet {unit}", label, vals, rng=rng)
    r += 1
text(ws, r, "빠진 지진: 산사태 후쿠시마·노토(양성만), 액상화 오사카(음성만) — AUC 계산 불가. "
            "DisasterNet 값은 seed 0~4 각각 AUC를 낸 뒤 평균, 오른쪽 두 열은 seed별 가중평균의 최소~최대. "
            "AdminDER·USGS는 무작위성이 없어 1회 값.", f_note, span=13)
ws.row_dimensions[r].height = 28
r += 1

# 표 2: 9개 지진 전체
r += 1
text(ws, r, "표 2. 9개 지진 전체 LOEO — AdminDER vs USGS (DisasterNet은 DPM이 없는 지진이 있어 비교 불가)", f_h2)
r += 1
header(ws, r, ["재해", "지진", "평가 시정촌", "양성", "음성", "USGS\n평균집계", "USGS\n최대집계", "변환 prior\nlog p̄ + log k",
                "AdminDER ①\n8개 지진 학습", "AdminDER ①\n+ 액상화 라벨 학습"])
r += 1
for hz in ("LS", "LQ"):
    n, p, q, us, tr = COL[hz]
    first = r
    for ev in ORDER:
        a1 = S1.loc[ev, tr]
        if pd.isna(a1):
            continue
        put(ws, r, 1, HZ[hz]); put(ws, r, 2, ev, align=left)
        put(ws, r, 3, int(S1.loc[ev, n])); put(ws, r, 4, int(S1.loc[ev, p])); put(ws, r, 5, int(S1.loc[ev, q]))
        put(ws, r, 6, float(S1.loc[ev, us]), fmt=NUM)
        put(ws, r, 7, MAX[hz][ev], fmt=NUM)
        put(ws, r, 8, float(S1.loc[ev, TP[hz]]), fmt=NUM)
        put(ws, r, 9, float(a1), fmt=NUM, fill=fill_trace, font=f_bold)
        put(ws, r, 10, float(S1L.loc[ev, tr]), fmt=NUM, fill=fill_trace)
        r += 1
    last = r - 1
    put(ws, r, 1, HZ[hz], font=f_bold, fill=fill_avg); put(ws, r, 2, "가중평균", font=f_bold, fill=fill_avg, align=left)
    for c in (3, 4, 5):
        L = get_column_letter(c)
        put(ws, r, c, f"=SUM({L}{first}:{L}{last})", font=f_bold, fill=fill_avg)
    for c in (6, 7, 8, 9, 10):
        L = get_column_letter(c)
        put(ws, r, c, f"=SUMPRODUCT($C{first}:$C{last},{L}{first}:{L}{last})/SUM($C{first}:$C{last})",
            fmt=NUM, font=f_bold, fill=fill_trace if c >= 9 else fill_avg)
    r += 2
r -= 1
text(ws, r, "빠진 지진: 산사태 니가타오키·이와테미야기·후쿠시마·노토(양성만), 액상화 니가타오키·이와테미야기(양성만)·오사카(음성만).", f_note)
r += 1

# 표 3: 산사태, 평가 지진의 cov 없이 채점 (교수님 요청 2026-11-15, cov0_loeo.py)
# cov0ref = 원래 cov로 채점(rq4nl_full·rq4d5_full과 같음을 아래·cov0_loeo.py에서 assert), cov0 = 평가 지진 행만 log cov = 0
C0 = {}
for m, S in (("d9", S1), ("d5", S2)):
    ref = pd.concat([pd.read_csv(f) for f in glob.glob(f"{REPO}/outputs/holdout_summary_cov0ref_{m}_*.csv")]).set_index("event")
    c0 = pd.concat([pd.read_csv(f) for f in glob.glob(f"{REPO}/outputs/holdout_summary_cov0_{m}_*.csv")]).set_index("event")
    ev_ls = [e for e in ORDER if e in S.index and pd.notna(S.loc[e, COL["LS"][4]])]
    assert sorted(ref.index) == sorted(c0.index) == sorted(ev_ls), (m, list(ref.index), ev_ls)
    for e in ev_ls:
        for c in ("auc_usgs_prior", "auc_A_own_prior", "auc_cov_kappa_prior", "auc_posterior_alpha_fit"):
            assert np.isclose(ref.loc[e, c], S.loc[e, c], atol=1e-9), (m, e, c)
        for c in ("n", "n_pos", "n_neg", "auc_usgs_prior", "auc_A_own_prior"):
            assert np.isclose(c0.loc[e, c], S.loc[e, c], atol=1e-9), (m, e, c)
        assert pd.notna(c0.loc[e, "auc_cov_kappa_prior"]) and pd.notna(c0.loc[e, "auc_posterior_alpha_fit"])
    C0[m] = (ev_ls, S, c0)

# ② 확장: 돗토리·니가타 2004는 DPM 5개 전부로 학습한 모델로 평가 (d5_eval_extra.py, 교수님 요청 A안)
EXTRA3 = ["2000 돗토리", "2004 니가타현주에쓰"]
X_ref = pd.concat([pd.read_csv(f"{REPO}/outputs/holdout_summary_d5all_{e.replace(' ', '')}.csv") for e in EXTRA3]).set_index("event")
X_c0 = pd.concat([pd.read_csv(f"{REPO}/outputs/holdout_summary_d5all_cov0_{e.replace(' ', '')}.csv") for e in EXTRA3]).set_index("event")
for e in EXTRA3:
    for c in ("n", "n_pos", "n_neg", "auc_usgs_prior", "auc_A_own_prior"):
        assert np.isclose(X_ref.loc[e, c], S1.loc[e, c], atol=1e-9) and np.isclose(X_c0.loc[e, c], S1.loc[e, c], atol=1e-9), (e, c)
fill_x = PatternFill("solid", fgColor="FFF9DB")  # DPM 5개 전부로 학습한 행

r += 1
text(ws, r, "표 3. 산사태 — 평가 지진의 판독 범위(cov) 없이 채점 (학습은 그대로, 테스트할 때만 평가 지진 cov = 1)", f_h2)
r += 1
text(ws, r, "학습은 AdminDER 최종 설정 그대로(평가 지진 행은 원래 학습에서 빠지므로 평가 지진 cov는 학습에 쓰인 적 없음). "
            "테스트할 때만 평가 지진 행의 log cov를 0으로 두고 prior·α_e 맞춤·사후를 다시 계산. "
            "cov가 있는 지진은 니가타 2004·구마모토·훗카이도(돗토리·오사카는 원래 cov = 1). 'cov 있음' 열은 표 1·2의 AdminDER와 같은 값. 주황 칸 = cov = 1 결과. "
            "② DPM 지진으로 학습: 구마모토·오사카·훗카이도는 DPM 5개 중 평가 지진을 뺀 4개로 학습(기존 ②), 노란 행(돗토리·니가타 2004)은 DPM 5개 전부로 학습(두 지진은 학습에 없음).",
     f_note)
ws.row_dimensions[r].height = 56
r += 1
header(ws, r, ["세트", "지진", "평가 시정촌", "양성", "음성", "USGS\n평균집계", "변환 prior\nlog p̄ + log k",
               "prior + cov + κ\n(cov 있음)", "AdminDER\n(cov 있음)", "AdminDER\n(평가 지진 cov = 1)"])
r += 1
BLOCKS = [
    ("① 9개 LOEO", [(e, "① 9개 LOEO\n(8개 학습)", S1, C0["d9"][2], None) for e in C0["d9"][0]]),
    ("② DPM 지진으로 학습",
     [(e, "② DPM 지진으로 학습\n(5개 학습)", X_ref, X_c0, fill_x) for e in EXTRA3]
     + [(e, "② DPM 지진으로 학습\n(4개 학습)", S2, C0["d5"][2], None) for e in C0["d5"][0]]),
]
for setname, rows in BLOCKS:
    assert [e for e, *_ in rows] == ["2000 돗토리", "2004 니가타현주에쓰", "2016 구마모토", "2018 오사카", "2018 훗카이도"]
    first = r
    for ev, lab, S, c0, fl in rows:
        put(ws, r, 1, lab, fill=fl); put(ws, r, 2, ev, align=left, fill=fl)
        put(ws, r, 3, int(S.loc[ev, "n"]), fill=fl); put(ws, r, 4, int(S.loc[ev, "n_pos"]), fill=fl); put(ws, r, 5, int(S.loc[ev, "n_neg"]), fill=fl)
        put(ws, r, 6, float(S.loc[ev, "auc_usgs_prior"]), fmt=NUM, fill=fl)
        put(ws, r, 7, float(S.loc[ev, "auc_A_own_prior"]), fmt=NUM, fill=fl)
        put(ws, r, 8, float(S.loc[ev, "auc_cov_kappa_prior"]), fmt=NUM, fill=fl)
        put(ws, r, 9, float(S.loc[ev, "auc_posterior_alpha_fit"]), fmt=NUM, fill=fill_trace, font=f_bold)
        put(ws, r, 10, float(c0.loc[ev, "auc_posterior_alpha_fit"]), fmt=NUM, fill=fill_q, font=f_bold)
        r += 1
    last = r - 1
    for label, a in (("가중평균", first), ("가중평균 (DPM 5개 지진만)", first + 2)):  # 아래 3행 = 구마모토·오사카·훗카이도
        put(ws, r, 1, setname, font=f_bold, fill=fill_avg); put(ws, r, 2, label, font=f_bold, fill=fill_avg, align=left)
        for c in (3, 4, 5):
            L = get_column_letter(c)
            put(ws, r, c, f"=SUM({L}{a}:{L}{last})", font=f_bold, fill=fill_avg)
        for c in range(6, 11):
            L = get_column_letter(c)
            fl = fill_q if c == 10 else (fill_trace if c == 9 else fill_avg)
            put(ws, r, c, f"=SUMPRODUCT($C{a}:$C{last},{L}{a}:{L}{last})/SUM($C{a}:$C{last})",
                fmt=NUM, font=f_bold, fill=fl)
        r += 1
text(ws, r, "결과 파일: pilotA/outputs/holdout_summary_cov0_{d9,d5}_*.csv (cov = 1), holdout_summary_cov0ref_{d9,d5}_*.csv (cov 있음, 기존 결과 재현 확인용), "
            "holdout_summary_d5all{,_cov0}_*.csv (② 돗토리·니가타). 스크립트 outputs/rq_scripts/cov0_loeo.py, d5_eval_extra.py.", f_note)
r += 1

# 표 4: ② 설정으로 DPM 5개 전부 학습 → DPM 없는 돗토리·니가타 2004 평가 (교수님 요청 2026-11-15 A안, d5_eval_extra.py)
EXTRA = ["2000 돗토리", "2004 니가타현주에쓰"]
DA = pd.concat([pd.read_csv(f"{REPO}/outputs/holdout_summary_d5all_{e.replace(' ', '')}.csv") for e in EXTRA]).set_index("event")
assert list(DA.index) == EXTRA
for e in EXTRA:  # 학습 없는 열과 평가 시정촌은 ①과 같아야 함
    for c in ("n", "n_pos", "n_neg", "auc_usgs_prior", "auc_A_own_prior",
              "n_lq", "n_pos_lq", "n_neg_lq", "auc_lq_usgs_prior", "auc_lq_A_own_prior"):
        assert np.isclose(DA.loc[e, c], S1.loc[e, c], atol=1e-9), (e, c)
r += 1
text(ws, r, "표 4. ② 설정으로 DPM 5개 지진 전부 학습 → DPM 없는 2000 돗토리·2004 니가타현주에쓰 평가", f_h2)
r += 1
text(ws, r, "모델·설정은 ②와 같음(λ_γ = λ_κ = 10, 3000 에폭, 산사태 라벨 학습, 액상화 라벨 미사용). 학습 = DPM 5개 전부(구마모토·오사카 북부·홋카이도 이부리 동부·후쿠시마 앞바다·노토반도), "
            "두 평가 지진은 학습에 없음 → LOEO와 같은 조건. 두 지진은 DPM이 없어 DisasterNet 결과는 없음. "
            "니가타 산사태는 평가 지진 cov = 1로 채점해도 1.000. 오른쪽 열은 표 2의 ① 값.", f_note)
ws.row_dimensions[r].height = 42
r += 1
header(ws, r, ["재해", "지진", "평가 시정촌", "양성", "음성", "USGS\n평균집계", "변환 prior\nlog p̄ + log k",
               "prior + cov + κ", "AdminDER ②\nDPM 5개 전부 학습", "AdminDER ①\n8개 지진 학습 (표 2)"])
r += 1
for hz, (n, p, q, us, tr) in (("LS", COL["LS"]), ("LQ", COL["LQ"])):
    for ev in EXTRA:
        put(ws, r, 1, HZ[hz]); put(ws, r, 2, ev, align=left)
        put(ws, r, 3, int(DA.loc[ev, n])); put(ws, r, 4, int(DA.loc[ev, p])); put(ws, r, 5, int(DA.loc[ev, q]))
        put(ws, r, 6, float(DA.loc[ev, us]), fmt=NUM)
        put(ws, r, 7, float(DA.loc[ev, TP[hz]]), fmt=NUM)
        if hz == "LS":
            put(ws, r, 8, float(DA.loc[ev, "auc_cov_kappa_prior"]), fmt=NUM)
        else:
            put(ws, r, 8, "–")
        put(ws, r, 9, float(DA.loc[ev, tr]), fmt=NUM, fill=fill_trace, font=f_bold)
        put(ws, r, 10, float(S1.loc[ev, tr]), fmt=NUM)
        r += 1
text(ws, r, "액상화 prior는 b만 학습(순위는 변환 prior와 같음)이라 'prior + cov + κ' 칸은 비움. 돗토리 액상화는 음성 1곳(비교 쌍 7개)이라 AUC가 크게 흔들림. "
            "결과 파일: pilotA/outputs/holdout_summary_d5all_*.csv (cov = 1 채점은 d5all_cov0_*), 스크립트 outputs/rq_scripts/d5_eval_extra.py.", f_note)
ws.row_dimensions[r].height = 28
r += 1

# 쟁점
r += 1
text(ws, r, "교수님께 여쭐 것", f_h2)
r += 1
qs = [
    "1. USGS 기준선 집계(산사태는 평균 0.729 / 최대 0.714로 어느 쪽이든 AdminDER 0.872가 높음). 액상화: 평균집계(AdminDER 입력과 같은 방식)면 AdminDER가 이기고(표 1 0.796 < 0.850), 최대집계(DisasterNet 실험 방식)면 진다(0.895 > 0.850). "
    "9개 지진 전체(표 2)에서도 최대집계 0.837 > AdminDER 0.804. 노토 차이가 특히 큼.",
    "2. DisasterNet: 시정촌 8개 + 확인 실험 2개, 칸 5개를 모두 넣음. 본문에 쓸 변형 선택 "
    "(예: 픽셀 = 칸 LOCALU, 시정촌 = DN, Soft = 시정촌 SOFTU_분산만).",
    "3. AdminDER 학습 범위: ① 9개 지진 LOEO(8개 학습)와 ② DPM 5개 안 LOEO(4개 학습) 중 본문에 쓸 것.",
]
for qtext in qs:
    c = text(ws, r, qtext)
    c.fill = fill_q
    ws.row_dimensions[r].height = 32
    r += 1

r += 1
text(ws, r, "알려드릴 것 (참고)", f_h2)
r += 1
for itext in [
    "• USGS prior 집계 방식이 다름: DisasterNet 입력은 산사태 = 시정촌 안 USGS 칸의 평균, 액상화 = 최댓값. "
    "AdminDER는 산사태·액상화 모두 평균. DisasterNet과 비교할 때 입력 조건이 같지 않음(형평성).",
    "• 라벨 사용이 다름: AdminDER는 학습 지진의 산사태 라벨만 학습에 쓰고 액상화 라벨은 쓰지 않음(평가 지진 라벨은 둘 다 안 씀). "
    "DisasterNet은 라벨 없이 지진마다 따로 학습.",
]:
    c = text(ws, r, itext)
    c.fill = fill_avg
    ws.row_dimensions[r].height = 32
    r += 1

r += 1
text(ws, r, "출처", f_h2)
r += 1
for line in [
    "AdminDER ①: pilotA/outputs/holdout_summary_rq4nl_full_*.csv · AdminDER ②: holdout_summary_rq4d5_full_*.csv (언니 결과와 소수 4자리까지 일치 확인).",
    "USGS 평균집계: 같은 CSV의 USGS prior AUC 열. USGS 최대집계: raw/재난프로젝트_시정촌별_USGS.xlsx의 LS_prior(최대)·LQ_prior(최대)로 같은 평가 시정촌에서 계산(액상화는 DisasterNet 문서 값과 일치).",
    "DisasterNet: 언니 예측 파일 Desktop/학부연구생/DisasterNet/민지언니 전달자료/disasternet_predictions (15개 폴더 × seed 0~4; 시정촌 = 클라우드 재실행, 칸 = 연구실 PC 결과)을 "
    "AdminDER와 같은 평가 시정촌·정답으로 채점. 채점 결과 pilotA/outputs/rq1/dn_auc_by_event.csv · dn_auc_weighted.csv.",
    "DisasterNet 대조: 인수인계 문서(DisasterNet 시정촌 실험.html · 칸 단위 실험.html)의 산사태·액상화 가중평균 26개와 지진별 값이 소수 셋째 자리까지 모두 일치.",
    "후쿠시마 액상화 双葉町(07546, 양성)은 DisasterNet 입력표 정답에는 있지만 pilotA 평가 행에 없어 모든 방법에서 빠짐(언니 보고 표도 같은 151곳 기준).",
]:
    text(ws, r, line, f_note)
    ws.row_dimensions[r].height = 28
    r += 1

widths = [17, 31, 14, 14, 14, 13, 14, 14, 14, 14, 13, 15, 15]
for i, w in enumerate(widths, 1):
    ws.column_dimensions[get_column_letter(i)].width = w
ws.freeze_panes = None
ws.sheet_view.showGridLines = False

# ---------- RQ2 ----------
# 숫자는 전부 언니 측정(2026-11-06~07, 같은 클라우드 VM)의 표와 답변에서 옮긴 값. 원자료 CSV(time_measured_20261107.csv)는 받지 않음.
s2 = wb["RQ2"]
r = 1
text(s2, r, "RQ2. AdminDER는 DisasterNet 대비 얼마나 경량인가?", f_title, span=8)
s2.row_dimensions[r].height = 26
r += 1
for line in [
    "논문: AdminDER: Inferring Earthquake-Induced Cascading Hazards from Web-Published Administrative Damage Statistics (모델 이름 TRACE → AdminDER로 변경).",
    "질문: 새 지진에서 사후확률을 얻기까지의 시간. AdminDER는 이미 학습된 모델로 추론만 하고, DisasterNet은 새 지진마다 그 지진으로 학습한 뒤 추론해야 함.",
    "측정: 언니가 같은 컴퓨터에서 다른 작업 없이 차례로 측정(2026-11-06~07). 모든 값은 DPM 있는 5개 지진의 합, seed 0, 1회 측정(반복 없음 → 편차 모름). 자료 읽는 시간 제외.",
    "AdminDER 추론 시간에는 α_e 맞춤(LBFGS)뿐 아니라 418행 전체 계산·AUC 계산·CSV 저장까지 들어 있어 실제보다 길게 잡힘(AdminDER에 불리한 방향).",
]:
    text(s2, r, line, f_note, span=8)
    s2.row_dimensions[r].height = 30
    r += 1

r += 1
text(s2, r, "표 1. 학습·추론 시간 (DPM 5개 지진 합, 초)", f_h2, span=8)
r += 1
header(s2, r, ["방법", "학습 (초)", "추론 (초)", "새 지진에 필요한 시간 (초)", "새 지진에 필요한 시간 (분)",
               "AdminDER ① 대비 배수", "새 지진에 필요한 일", "비고"])
r += 1
t1 = r
TIMES = [  # (방법, 학습, 추론, AdminDER인가, 필요한 일, 비고)
    ("AdminDER ① 8개 지진 학습", 67.9, 0.29, True, "추론만", "학습은 처음 한 번만 (폴드 5개 합, 폴드당 12.7~14.8초)"),
    ("AdminDER ② DPM 4개 지진 학습", 59.8, 0.31, True, "추론만", "학습은 처음 한 번만 (폴드 5개 합, 폴드당 11.3~12.7초)"),
    ("DisasterNet 시정촌 SOFTU_분산만", 61.0, 0.013, False, "학습 + 추론", "지진마다 새로 학습"),
    ("DisasterNet 칸 LOCALU", 5405.8, 40.13, False, "학습 + 추론", "지진마다 새로 학습 (지진별 시간은 표 2)"),
]
for name, tr, inf, is_trace, need, note in TIMES:
    fill = fill_trace if is_trace else None
    put(s2, r, 1, name, fill=fill, align=left, font=f_bold if is_trace else f_body)
    put(s2, r, 2, tr, fmt="#,##0.0", fill=fill)
    put(s2, r, 3, inf, fmt="0.000", fill=fill)
    put(s2, r, 4, f"=C{r}" if is_trace else f"=B{r}+C{r}", fmt="#,##0.000", fill=fill, font=f_bold)
    put(s2, r, 5, f"=D{r}/60", fmt="0.00", fill=fill)
    put(s2, r, 6, f"=D{r}/$D${t1}", fmt='#,##0.0"배"', fill=fill)
    put(s2, r, 7, need, fill=fill)
    put(s2, r, 8, note, fill=fill, align=left, font=f_note)
    r += 1
text(s2, r, "배수는 언니 표의 반올림 값(예: 추론 0.29초)으로 계산해서 대략치. "
            "논리구조 정의대로 AdminDER는 추론 시간, DisasterNet은 학습 + 추론 시간을 비교.", f_note, span=8)
s2.row_dimensions[r].height = 28
r += 2

text(s2, r, "표 2. DisasterNet 칸 LOCALU 지진별 시간 (seed 0, 지진을 하나씩 차례로 실행)", f_h2, span=8)
r += 1
header(s2, r, ["지진", "칸 수", "학습 (초)", "추론 (초)", "학습 + 추론 (분)"])
r += 1
first = r
for ev, n, tr, inf in [("2016 구마모토", 96404, 521.0, 5.06), ("2018 오사카", 44811, 263.1, 2.12),
                       ("2018 훗카이도", 294110, 1560.4, 9.06), ("2021 후쿠시마", 269604, 1331.4, 10.97),
                       ("2024 노토반도", 320110, 1729.9, 12.92)]:
    put(s2, r, 1, ev, align=left); put(s2, r, 2, n, fmt="#,##0")
    put(s2, r, 3, tr, fmt="#,##0.0"); put(s2, r, 4, inf, fmt="0.00")
    put(s2, r, 5, f"=(C{r}+D{r})/60", fmt="0.0")
    r += 1
last = r - 1
put(s2, r, 1, "합", font=f_bold, fill=fill_avg, align=left)
put(s2, r, 2, f"=SUM(B{first}:B{last})", fmt="#,##0", font=f_bold, fill=fill_avg)
put(s2, r, 3, f"=SUM(C{first}:C{last})", fmt="#,##0.0", font=f_bold, fill=fill_avg)
put(s2, r, 4, f"=SUM(D{first}:D{last})", fmt="0.00", font=f_bold, fill=fill_avg)
put(s2, r, 5, f"=(C{r}+D{r})/60", fmt="0.0", font=f_bold, fill=fill_avg)
sum_row = r
r += 1
text(s2, r, "합이 표 1의 LOCALU(학습 5,405.8초 · 추론 40.13초)와 같아야 함. 칸 수에 따라 지진 하나당 약 4~29분.", f_note, span=8)
r += 2

text(s2, r, "표 3. 정확도 (RQ1 표 1에서 연결, DPM 5개 지진 가중평균 AUC)", f_h2, span=8)
r += 1
header(s2, r, ["방법", "산사태 AUC", "액상화 AUC"])
r += 1
for name, key in [("AdminDER ① 8개 지진 학습", ("AdminDER", "① 8개 지진 학습 (9개 LOEO)")),
                  ("AdminDER ② DPM 4개 지진 학습", ("AdminDER", "② DPM 4개 지진 학습 (5개 LOEO)")),
                  ("DisasterNet 시정촌 SOFTU_분산만", ("DisasterNet 시정촌", "SOFTU_분산만")),
                  ("DisasterNet 칸 LOCALU", ("DisasterNet 칸", "LOCALU"))]:
    rr = ROWS[key]
    is_trace = key[0] == "AdminDER"
    put(s2, r, 1, name, align=left, fill=fill_trace if is_trace else None, font=f_bold if is_trace else f_body)
    put(s2, r, 2, f"=RQ1!F{rr}", fmt=NUM, fill=fill_trace if is_trace else None)
    put(s2, r, 3, f"=RQ1!K{rr}", fmt=NUM, fill=fill_trace if is_trace else None)
    r += 1
text(s2, r, "언니 표의 '전체 AUC'(0.855 등)는 산사태와 액상화를 섞은 값이라 여기서는 나눠서 보임.", f_note, span=8)
r += 2

text(s2, r, "표 4. 측정 환경", f_h2, span=8)
r += 1
header(s2, r, ["항목", "내용"])
r += 1
for k, v in [("컴퓨터", "클라우드 가상 컴퓨터 (Claude 실행 환경)"), ("CPU", "Intel Xeon Processor @ 2.10GHz, 4코어 (코어당 1스레드)"),
             ("GPU", "없음 (CPU만 사용)"), ("메모리", "15GB"), ("OS", "Ubuntu 24.04.5 LTS"),
             ("소프트웨어", "Python 3.13.16, PyTorch 2.14.1"), ("계산 스레드", "4"),
             ("수렴 기준", "AdminDER · DisasterNet 모두 3000 에폭 고정 (조기 종료 없음)")]:
    put(s2, r, 1, k, align=left, font=f_bold); put(s2, r, 2, v, align=left)
    s2.merge_cells(start_row=r, start_column=2, end_row=r, end_column=5)
    r += 1
r += 1

text(s2, r, "교수님께 여쭐 것 (보류 중)", f_h2, span=8)
r += 1
for qtext in [
    "1. 편차를 보이기 위해 같은 컴퓨터에서 3회 반복 측정할지 (DisasterNet 칸 단위는 1회 약 90분).",
    "2. DisasterNet을 GPU로 돌리면 격차가 줄 수 있음 — GPU 측정도 추가할지.",
    "3. 표 주석: '지진 5개 합, seed 0, 1회 측정, AdminDER 추론에 α_e 맞춤 포함'으로 적을지.",
]:
    c = text(s2, r, qtext, span=8)
    c.fill = fill_q
    s2.row_dimensions[r].height = 22
    r += 1
r += 1
text(s2, r, "출처", f_h2, span=8)
r += 1
for line in [
    "언니 시간 측정 표·답변(2026-11-13 전달): 측정 코드 disasternet/time_measure/, 결과 outputs/disasternet/time_measured_20261107.csv (언니 저장소, 이 PC에는 없음).",
    "선배 문서의 칸 단위 '약 1시간 25분'은 연구실 PC에서 지진 5개를 동시에 돌린 경과 시간이라 이 표와 섞지 않음.",
]:
    text(s2, r, line, f_note, span=8)
    s2.row_dimensions[r].height = 28
    r += 1
for i, w in enumerate([34, 12, 12, 16, 14, 14, 14, 44], 1):
    s2.column_dimensions[get_column_letter(i)].width = w
s2.sheet_view.showGridLines = False

# ---------- RQ3 ----------
# γ: 기존 실험(λ_γ = 10, 3000 에폭) 값만 씀.
#  전체판 = outputs/rq3/gamma_full9.csv (지금 코드로 재학습, 10월 03b 파일과 1e-17까지 같음)
#  폴드별 = outputs/언니전달_액상화J_설정/03_폴드별_전체파라미터_nolabels.csv (9개 지진 LOEO, rq4nl full과 같은 학습)
s3 = wb["RQ3"]
KOR = ["사망", "중상", "경상", "전파", "반파", "일부파손"]
G9 = pd.read_csv(f"{REPO}/outputs/rq3/gamma_full9.csv").set_index("label")
FOLD = pd.read_csv(f"{REPO}/outputs/언니전달_액상화J_설정/03_폴드별_전체파라미터_nolabels.csv")
assert np.allclose(G9.gamma_ls, G9.gamma_ls_oct) and np.allclose(G9.gamma_lq, G9.gamma_lq_oct)
# 부트스트랩 95% 구간 (교수님 결정 2026-11-13; rq3_bootstrap.py 1000회 → rq3_bootstrap_ci.py)
CI = pd.read_csv(f"{REPO}/outputs/rq3/bootstrap_ci.csv").set_index(["재해", "label"])
for (hz, k), row in CI.iterrows():  # 점추정이 표의 γ와 같은지
    assert np.isclose(row.gamma, G9.loc[k, "gamma_ls" if hz == "LS" else "gamma_lq"]), (hz, k)
assert len(CI) == 12
r = 1
text(s3, r, "RQ3. AdminDER는 후속 재난이 피해에 미친 영향을 설명 가능한가?", f_title, span=13)
s3.row_dimensions[r].height = 26
r += 1
for line in [
    "논문: AdminDER: Inferring Earthquake-Induced Cascading Hazards from Web-Published Administrative Damage Statistics.",
    "피해 식: log μ = log E + α_c + α_e + β_c·log PGV + δ_c·z_wood + γ^LS_c·LS + γ^LQ_c·LQ (c = 피해 채널 6개). "
    "산사태(LS) 또는 액상화(LQ)가 난 시정촌은 그 채널의 기대 피해 건수가 exp(γ)배 → 이것이 '배율'.",
    "γ = softplus(학습값) ≥ 0으로 제약(배율은 항상 1 이상). 손실에 λ_γ·Σγ² (λ_γ = 10)를 더해 γ를 0 쪽으로 당김. 설정은 RQ1과 같은 최종 설정, 3000 에폭.",
]:
    text(s3, r, line, f_note, span=13)
    s3.row_dimensions[r].height = 30
    r += 1

# 액상화 라벨 포함판(원고 설정, 교수님 2026-11-17 "Figure 3은 액상화 라벨 포함 버전으로") — 표 3·4
#  전체판 = outputs/rq3/lql/gamma_full9_lql.csv (rq3_lql.py check, 10월 03b labels 파일과 1e-16까지 같음)
#  폴드별 = 03_폴드별_전체파라미터_labels.csv (지금 코드로 오사카 폴드 재학습해 1e-16까지 같음 확인)
#  95% 구간 = outputs/rq3/lql/bootstrap_ci_lql.csv (1000회, 재표집 시정촌은 기존 제약판과 회차별 동일)
G9L = pd.read_csv(f"{REPO}/outputs/rq3/lql/gamma_full9_lql.csv").set_index("label")
FOLDL = pd.read_csv(f"{REPO}/outputs/언니전달_액상화J_설정/03_폴드별_전체파라미터_labels.csv")
assert np.allclose(G9L.gamma_ls, G9L.gamma_ls_oct) and np.allclose(G9L.gamma_lq, G9L.gamma_lq_oct)
CIL = pd.read_csv(f"{REPO}/outputs/rq3/lql/bootstrap_ci_lql.csv").set_index(["재해", "label"])
for (hz, k), row in CIL.iterrows():
    assert np.isclose(row.gamma, G9L.loc[k, "gamma_ls" if hz == "LS" else "gamma_lq"]), (hz, k)
assert len(CIL) == 12


def gamma_tables(r, G9, FOLD, CI, n1, n2, tag):
    """표 n1(배율 + 폴드 범위 + 95% 구간)과 표 n2(폴드별 γ). 표 1·2와 같은 양식."""
    folds = [e for e in ORDER if e in set(FOLD.fold)]
    assert len(folds) == 9
    r += 1
    text(s3, r, f"표 {n1}. 피해 채널별 배율 exp(γ){tag} — 9개 지진 전체로 학습한 모델, 폴드 범위는 9개 LOEO 폴드의 최소~최대", f_h2, span=13)
    r += 1
    r = gamma_body(r, G9, FOLD, CI, folds, n2, tag)
    return r


def gamma_body(r, G9, FOLD, CI, folds, n2, tag):
    # 머리글 2줄: 1~9열은 위아래 통합, 10~13열은 위에 "○○ 배율 95% 구간"(가로 통합) + 아래 하한/상한
    header(s3, r, ["피해 채널", "산사태 γ", "산사태 배율", "산사태 배율\n폴드 최소", "산사태 배율\n폴드 최대",
                   "액상화 γ", "액상화 배율", "액상화 배율\n폴드 최소", "액상화 배율\n폴드 최대",
                   "산사태 배율 95% 구간", "", "액상화 배율 95% 구간", ""])
    header(s3, r + 1, [""] * 9 + ["하한", "상한", "하한", "상한"])
    s3.row_dimensions[r].height = 24
    s3.row_dimensions[r + 1].height = 24
    for c in range(1, 10):
        s3.merge_cells(start_row=r, start_column=c, end_row=r + 1, end_column=c)
    s3.merge_cells(start_row=r, start_column=10, end_row=r, end_column=11)
    s3.merge_cells(start_row=r, start_column=12, end_row=r, end_column=13)
    r += 2
    t1_first = r
    t2_first = t1_first + len(KOR) + 4  # 표 2 첫 데이터 행 (아래 배치와 맞춤, assert로 확인)
    t2_last = t2_first + len(folds) - 1
    for i, k in enumerate(KOR):
        ls_col = get_column_letter(2 + i)        # 표 2: B~G = 산사태 γ, H~M = 액상화 γ
        lq_col = get_column_letter(8 + i)
        put(s3, r, 1, k, align=left, font=f_bold)
        put(s3, r, 2, float(G9.loc[k, "gamma_ls"]), fmt=NUM)
        put(s3, r, 3, f"=EXP(B{r})", fmt=NUM, font=f_bold, fill=fill_trace)
        put(s3, r, 4, f"=EXP(MIN({ls_col}{t2_first}:{ls_col}{t2_last}))", fmt=NUM)
        put(s3, r, 5, f"=EXP(MAX({ls_col}{t2_first}:{ls_col}{t2_last}))", fmt=NUM)
        put(s3, r, 6, float(G9.loc[k, "gamma_lq"]), fmt=NUM)
        put(s3, r, 7, f"=EXP(F{r})", fmt=NUM, font=f_bold, fill=fill_trace)
        put(s3, r, 8, f"=EXP(MIN({lq_col}{t2_first}:{lq_col}{t2_last}))", fmt=NUM)
        put(s3, r, 9, f"=EXP(MAX({lq_col}{t2_first}:{lq_col}{t2_last}))", fmt=NUM)
        for j, (hz, q) in enumerate([("LS", "배율_2.5%"), ("LS", "배율_97.5%"), ("LQ", "배율_2.5%"), ("LQ", "배율_97.5%")]):
            put(s3, r, 10 + j, float(CI.loc[(hz, k), q]), fmt=NUM)
        r += 1
    text(s3, r, "폴드 범위는 학습 지진을 바꿔도 얼마나 안정적인지 보여주는 값이며 신뢰구간이 아님. "
                "95% 구간: 시정촌 부트스트랩 1000회(지진마다 그 지진의 시정촌을 같은 수만큼 복원추출, 회차마다 같은 설정으로 9개 지진 전체 재학습)의 "
                "γ 2.5%·97.5% 퍼센타일을 exp 한 값. 배율(점추정)은 원래 데이터로 학습한 값.",
         f_note, span=13)
    s3.row_dimensions[r].height = 42
    r += 2
    text(s3, r, f"표 {n2}. 폴드별 γ{tag} (9개 지진 LOEO, 평가 지진을 뺀 8개로 학습, λ_γ = 10, 3000 에폭)", f_h2, span=13)
    r += 1
    header(s3, r, ["학습에서 뺀 지진"] + [f"산사태 γ\n{k}" for k in KOR] + [f"액상화 γ\n{k}" for k in KOR])
    r += 1
    assert r == t2_first, (r, t2_first)
    for ev in folds:
        g = FOLD[FOLD.fold == ev]
        put(s3, r, 1, ev, align=left)
        for i, k in enumerate(KOR):
            put(s3, r, 2 + i, float(g[(g.group == "gamma_LS") & (g.label == k)].value.iloc[0]), fmt=NUM)
            put(s3, r, 8 + i, float(g[(g.group == "gamma_LQ") & (g.label == k)].value.iloc[0]), fmt=NUM)
        r += 1
    return r


folds = [e for e in ORDER if e in set(FOLD.fold)]  # RQ5에서도 씀
r = gamma_tables(r, G9, FOLD, CI, 1, 2, "")
r += 1
text(s3, r, "표 3·4는 원고 설정(산사태·액상화 라벨 모두 학습)으로 다시 낸 값. 교수님 요청(2026-11-17): 원고 Figure 3은 액상화 라벨 포함 버전으로. "
            "나머지 설정(γ = softplus ≥ 0 제약, λ_γ = λ_κ = 10, 3000 에폭, 부트스트랩 1000회·재표집 시정촌)은 표 1·2와 같음.", f_note, span=13)
s3.row_dimensions[r].height = 30
r += 1
r = gamma_tables(r, G9L, FOLDL, CIL, 3, 4, " (액상화 라벨 포함판)")
r += 1
text(s3, r, "교수님께 여쭐 것", f_h2, span=13)
r += 1
for qtext in [
    "1. 신뢰구간 방법: 라플라스 근사(학습 1회, 손실 곡률로 계산; γ의 정규분포 prior와 맞음) vs 시정촌 부트스트랩(여러 번 재학습).",
    "2. 배율 크기는 λ_γ에 크게 좌우됨(RQ5 시트 참고: 예) 액상화 전파 배율이 λ_γ = 0.1이면 훨씬 큼). 크기를 주장할지, 순위·방향만 주장할지.",
    "3. γ ≥ 0 제약 때문에 '후속 재난이 피해를 줄였다'는 결론은 구조상 나올 수 없음 — 본문에 명시할지.",
]:
    c = text(s3, r, qtext, span=13)
    c.fill = fill_q
    s3.row_dimensions[r].height = 24
    r += 1
r += 1
text(s3, r, "출처", f_h2, span=13)
r += 1
for line in [
    "전체판 γ: pilotA/outputs/rq3/gamma_full9.csv (지금 코드로 다시 학습한 값, 10월 파일 03b_전체판(분리없음)_파라미터_nolabels.csv와 같음).",
    "폴드별 γ: pilotA/outputs/언니전달_액상화J_설정/03_폴드별_전체파라미터_nolabels.csv (RQ1·RQ4의 AdminDER 결과와 같은 학습).",
    "표 3·4(액상화 라벨 포함판): 전체판 pilotA/outputs/rq3/lql/gamma_full9_lql.csv(10월 03b labels 파일과 같음), 폴드별 03_폴드별_전체파라미터_labels.csv, "
    "95% 구간 pilotA/outputs/rq3/lql/bootstrap_ci_lql.csv (스크립트 outputs/rq_scripts/rq3_lql.py).",
]:
    text(s3, r, line, f_note, span=13)
    r += 1
for i, w in enumerate([22] + [12] * 12, 1):
    s3.column_dimensions[get_column_letter(i)].width = w
s3.sheet_view.showGridLines = False

# ---------- RQ4 ----------
# 기존 RQ4 실행 결과만: outputs/holdout_summary_rq4nl_<조건>_* (① 9개 LOEO, 8개 학습), rq4d5 (② DPM 5개 LOEO, 4개 학습)
s4 = wb["RQ4"]
CONDS = [  # (태그, 층위, 이름, 무엇을 바꿨나)
    ("full", "기준", "AdminDER (전체)", "최종 설정 그대로"),
    ("uniform", "입력 (Idea 1)", "prior 균등 (0.5 고정)", "모든 시정촌 사전확률을 0.5로"),
    ("umean", "입력 (Idea 1)", "prior 균등 (학습 지진 평균)", "학습 시정촌의 원래 prior 값(κ = 0, b = 0) 평균 하나로 고정"),
    ("ulearn", "입력 (Idea 1)", "prior 균등 (학습으로 정함)", "위 평균에서 출발해 재해마다 상수 1개 학습"),
    ("nopgv", "입력 (Idea 1)", "흔들림(PGV) 항 제거", "피해 식에서 β·log PGV 제거"),
    ("poisson", "구조 (Idea 2)", "포아송 분포", "음이항 → 포아송 (과분산 없음)"),
    ("noexp", "구조 (Idea 2)", "노출 offset 제거", "μ = E·λ 대신 μ = λ (세대 수로 규모 보정 안 함)"),
    ("single", "학습 (Idea 3)", "이벤트별 단독 학습", "평가 지진 행만으로, 라벨 없이 학습"),
]
HN4 = {"full": "TRACE (전체)", "uniform": "prior 균등 (0.5)", "umean": "prior 균등 (평균)", "ulearn": "prior 균등 (학습)",
       "nopgv": "흔들림 항 제거", "poisson": "포아송", "noexp": "노출 offset 제거", "single": "이벤트별 단독 학습"}
RES4 = {}
for tag in ("rq4nl", "rq4d5"):
    for c, *_ in CONDS:
        RES4[(tag, c)] = summary(f"{tag}_{c}")

# 언니 결과와 대조 (지진 × 재해 AUC, 소수 4자리)
MATCH = {}
for tag, fname in (("rq4nl", "ablation_result_지진별.csv"), ("rq4d5", "ablation_result_dpm5_지진별.csv")):
    her = pd.read_csv(rf"C:\Users\PC\Desktop\RQ4_ablation_비교용\{fname}")
    ok = tot = 0
    for c, *_ in CONDS:
        d = RES4[(tag, c)].reset_index()
        mine = pd.concat([
            d[["event", COL["LS"][4]]].rename(columns={COL["LS"][4]: "m"}).assign(재해="LS"),
            d[["event", COL["LQ"][4]]].rename(columns={COL["LQ"][4]: "m"}).assign(재해="LQ"),
        ]).dropna().rename(columns={"event": "지진"})
        x = her[her["설정"] == HN4[c]].merge(mine, on=["지진", "재해"], how="outer")
        ok += int((x.m.round(4) == x.AUC).sum())
        tot += len(x)
    MATCH[tag] = (ok, tot)
assert MATCH["rq4nl"][0] == MATCH["rq4nl"][1] and MATCH["rq4d5"][0] == MATCH["rq4d5"][1], MATCH

r = 1
text(s4, r, "RQ4. 각 층위의 설계는 정확도에 얼마나 기여하는가? (Ablation study)", f_title, span=17)
s4.row_dimensions[r].height = 26
r += 1
for line in [
    "논문: AdminDER: Inferring Earthquake-Induced Cascading Hazards from Web-Published Administrative Damage Statistics.",
    "방법: AdminDER 최종 설정에서 설계 하나만 빼거나 바꾸고 나머지는 그대로 두어 다시 학습·평가. 평가 방식은 RQ1과 같음(LOEO, 새 지진 α_e만 피해로 맞춘 사후확률, 지진 안 AUC를 평가 시정촌 수로 가중평균).",
    "모델이 결정적(초기값 상수, 전체 배치, 샘플링 없음)이라 seed 반복은 의미 없음 → 조건마다 1회 실행값. 차이의 유의성은 부트스트랩이 필요(아직 안 함).",
    f"언니 결과와 대조: 지진 × 재해 AUC가 ① {MATCH['rq4nl'][0]}/{MATCH['rq4nl'][1]}, ② {MATCH['rq4d5'][0]}/{MATCH['rq4d5'][1]} 소수 4자리까지 모두 일치.",
]:
    text(s4, r, line, f_note, span=17)
    s4.row_dimensions[r].height = 30
    r += 1

r += 1
text(s4, r, "조건 설명", f_h2, span=17)
r += 1
header(s4, r, ["층위", "조건", "무엇을 바꿨나"])
s4.merge_cells(start_row=r, start_column=3, end_row=r, end_column=10)
r += 1
for c, layer, name, what in CONDS:
    put(s4, r, 1, layer, align=left); put(s4, r, 2, name, align=left, font=f_bold if c == "full" else f_body)
    put(s4, r, 3, what, align=left)
    s4.merge_cells(start_row=r, start_column=3, end_row=r, end_column=10)
    r += 1


def ablation_table(r, tag, title):
    S = RES4[(tag, "full")]
    evs = {h: [e for e in ORDER if e in S.index and pd.notna(S.loc[e, COL[h][4]])] for h in ("LS", "LQ")}
    for c, *_ in CONDS:  # 조건마다 같은 지진·같은 평가 시정촌인지 확인
        for h in ("LS", "LQ"):
            R = RES4[(tag, c)]
            assert [e for e in ORDER if e in R.index and pd.notna(R.loc[e, COL[h][4]])] == evs[h], (tag, c, h)
            for e in evs[h]:
                assert R.loc[e, COL[h][0]] == S.loc[e, COL[h][0]], (tag, c, h, e)
    cpos, c0 = {}, 3
    for e in evs["LS"]:
        cpos[("LS", e)] = c0; c0 += 1
    wls = c0; c0 += 1
    for e in evs["LQ"]:
        cpos[("LQ", e)] = c0; c0 += 1
    wlq = c0; c0 += 1
    dls, dlq = c0, c0 + 1
    ncol = dlq
    text(s4, r, title, f_h2, span=max(ncol, 13))
    r += 1
    header(s4, r, ["층위", "조건"] + [f"산사태\n{e}" for e in evs["LS"]] + ["산사태\n가중평균"]
           + [f"액상화\n{e}" for e in evs["LQ"]] + ["액상화\n가중평균", "산사태\n기준 대비 Δ", "액상화\n기준 대비 Δ"])
    r += 1
    nrow = r
    put(s4, r, 1, "", fill=fill_avg); put(s4, r, 2, "평가 시정촌 수", font=f_bold, fill=fill_avg, align=left)
    for (h, e), c in cpos.items():
        put(s4, r, c, int(S.loc[e, COL[h][0]]), font=f_bold, fill=fill_avg)
    for h, wc in (("LS", wls), ("LQ", wlq)):
        cols = [c for (hh, _), c in cpos.items() if hh == h]
        put(s4, r, wc, f"=SUM({get_column_letter(min(cols))}{r}:{get_column_letter(max(cols))}{r})", font=f_bold, fill=fill_avg)
    put(s4, r, dls, "", fill=fill_avg); put(s4, r, dlq, "", fill=fill_avg)
    r += 1
    put(s4, r, 1, "", fill=fill_avg); put(s4, r, 2, "양성 / 음성", fill=fill_avg, align=left)
    for (h, e), c in cpos.items():
        put(s4, r, c, f"{int(S.loc[e, COL[h][1]])} / {int(S.loc[e, COL[h][2]])}", fill=fill_avg)
    for h, wc in (("LS", wls), ("LQ", wlq)):
        put(s4, r, wc, f"{sum(int(S.loc[e, COL[h][1]]) for e in evs[h])} / {sum(int(S.loc[e, COL[h][2]]) for e in evs[h])}",
            fill=fill_avg)
    put(s4, r, dls, "", fill=fill_avg); put(s4, r, dlq, "", fill=fill_avg)
    r += 1
    full_row = r
    for c, layer, name, _ in CONDS:
        R = RES4[(tag, c)]
        is_full = c == "full"
        fill = fill_trace if is_full else None
        put(s4, r, 1, layer, fill=fill, align=left); put(s4, r, 2, name, fill=fill, align=left, font=f_bold if is_full else f_body)
        for (h, e), col in cpos.items():
            put(s4, r, col, float(R.loc[e, COL[h][4]]), fmt=NUM, fill=fill)
        for h, wc in (("LS", wls), ("LQ", wlq)):
            cols = [col for (hh, _), col in cpos.items() if hh == h]
            a, b = get_column_letter(min(cols)), get_column_letter(max(cols))
            put(s4, r, wc, f"=SUMPRODUCT(${a}${nrow}:${b}${nrow},{a}{r}:{b}{r})/SUM(${a}${nrow}:${b}${nrow})",
                fmt=NUM, font=f_bold, fill=fill or fill_avg)
        for wc, dc in ((wls, dls), (wlq, dlq)):
            L = get_column_letter(wc)
            put(s4, r, dc, f"={L}{r}-{L}${full_row}", fmt='+0.000;-0.000;0.000', fill=fill)
        r += 1
    return r, ncol


r += 1
r, nc1 = ablation_table(r, "rq4nl", "표 1. ① 9개 지진 LOEO (평가 지진을 뺀 8개 지진으로 학습) — 본문 후보")
text(s4, r, "Δ = 그 조건의 가중평균 − AdminDER(전체) 가중평균. 음수면 그 설계를 뺐을 때 나빠짐(= 필요한 설계), 양수면 빼도 좋아짐.", f_note, span=17)
r += 2
r, nc2 = ablation_table(r, "rq4d5", "표 2. ② DPM 있는 5개 지진 LOEO (평가 지진을 뺀 4개 지진으로 학습) — 언니가 함께 돌린 보조 결과")
r += 1

text(s4, r, "교수님께 여쭐 것", f_h2, span=17)
r += 1
for qtext in [
    "1. '이벤트별 단독 학습' 정의: 평가 지진 행만으로 라벨 없이 학습(언니·우리 같은 정의). 크로스이벤트 공유와 라벨 사용이 함께 빠져 두 효과가 나뉘지 않음 — 의도와 맞는지.",
    "2. 방향이 갈리는 조건: 흔들림 항 제거(산사태 ↓, 액상화 ↑), 노출 offset 제거·단독 학습(산사태 ↑, 액상화 ↓) — 어떻게 서술할지.",
    "3. 균등 prior는 3가지(0.5 / 평균 / 학습) 중 무엇을 보고할지. 셋 다 비슷하게 크게 떨어짐 → 수준이 아니라 시정촌 간 순위 정보가 중요하다는 근거.",
    "4. ① 9개 지진 LOEO와 ② DPM 5개 LOEO 중 본문에 쓸 것, 부트스트랩으로 유의성을 볼지.",
]:
    c = text(s4, r, qtext, span=17)
    c.fill = fill_q
    s4.row_dimensions[r].height = 24
    r += 1
r += 1
text(s4, r, "출처", f_h2, span=17)
r += 1
for line in [
    "AdminDER 결과: pilotA/outputs/holdout_summary_rq4nl_<조건>_*.csv (①), holdout_summary_rq4d5_<조건>_*.csv (②). 비교용 묶음 outputs/rq4/RQ4_ablation_비교용.zip.",
    "언니 결과: Desktop/RQ4_ablation_비교용/ablation_result_지진별.csv, ablation_result_dpm5_지진별.csv.",
]:
    text(s4, r, line, f_note, span=17)
    r += 1
for i, w in enumerate([15, 27] + [12] * 15, 1):
    s4.column_dimensions[get_column_letter(i)].width = w
s4.sheet_view.showGridLines = False

# ---------- RQ5 ----------
# 기존 실행 결과만: λ_γ 0.1·1 = outputs/holdout_summary_rq5l{0.1,1}_* + outputs/rq5/gamma_lam{0.1,1}.csv (2026-11-13, λ_κ = 10 고정)
#                  λ_γ 10 = rq4nl_full (RQ1·RQ4와 같은 결과) + 03_폴드별_전체파라미터_nolabels.csv
s5 = wb["RQ5"]
LAMS = [("0.1", "rq5l0.1"), ("1", "rq5l1"), ("10", "rq4nl_full")]
RES5 = {lam: summary(tag) for lam, tag in LAMS}
ENG = {"사망": "death", "중상": "serious_injury", "경상": "minor_injury", "전파": "full_collapse",
       "반파": "half_collapse", "일부파손": "partial_damage"}
GAM = {}
for lam in ("0.1", "1"):
    g = pd.read_csv(f"{REPO}/outputs/rq5/gamma_lam{lam}.csv")
    GAM[lam] = {(ev, h, k): float(g[(g.fold == ev) & (g.channel == ENG[k])][f"gamma_{h.lower()}"].iloc[0])
                for ev in folds for h in ("LS", "LQ") for k in KOR}
GAM["10"] = {(ev, h, k): float(FOLD[(FOLD.fold == ev) & (FOLD.group == f"gamma_{h}") & (FOLD.label == k)].value.iloc[0])
             for ev in folds for h in ("LS", "LQ") for k in KOR}

r = 1
text(s5, r, "RQ5. AdminDER는 주요 하이퍼파라미터에 얼마나 민감한가? (Parameter sensitivity)", f_title, span=17)
s5.row_dimensions[r].height = 26
r += 1
for line in [
    "논문: AdminDER: Inferring Earthquake-Induced Cascading Hazards from Web-Published Administrative Damage Statistics.",
    "λ_γ = γ L2 정규화 강도(손실에 λ_γ·Σγ²). {0.1, 1, 10}만 바꾸고 나머지는 최종 설정 그대로(λ_κ = 10 고정, 3000 에폭). λ_γ = 10이 최종 설정(RQ1·RQ4와 같은 결과).",
    "평가는 RQ1과 같음(9개 지진 LOEO, 8개 지진 학습, 새 지진 α_e만 피해로 맞춘 사후확률, 지진 안 AUC를 평가 시정촌 수로 가중평균).",
]:
    text(s5, r, line, f_note, span=17)
    s5.row_dimensions[r].height = 30
    r += 1

# 표 1: λ별 AUC
r += 1
text(s5, r, "표 1. λ_γ별 AUC (9개 지진 LOEO)", f_h2, span=17)
r += 1
S10 = RES5["10"]
ev5 = {h: [e for e in ORDER if pd.notna(S10.loc[e, COL[h][4]])] for h in ("LS", "LQ")}
for lam, _ in LAMS:
    for h in ("LS", "LQ"):
        R = RES5[lam]
        assert [e for e in ORDER if pd.notna(R.loc[e, COL[h][4]])] == ev5[h], (lam, h)
        for e in ev5[h]:
            assert R.loc[e, COL[h][0]] == S10.loc[e, COL[h][0]]
cp, c0 = {}, 2
for e in ev5["LS"]:
    cp[("LS", e)] = c0; c0 += 1
w5ls = c0; c0 += 1
for e in ev5["LQ"]:
    cp[("LQ", e)] = c0; c0 += 1
w5lq = c0; c0 += 1
d5ls, d5lq = c0, c0 + 1
header(s5, r, ["λ_γ"] + [f"산사태\n{e}" for e in ev5["LS"]] + ["산사태\n가중평균"] + [f"액상화\n{e}" for e in ev5["LQ"]]
       + ["액상화\n가중평균", "산사태\nλ_γ = 10 대비 Δ", "액상화\nλ_γ = 10 대비 Δ"])
r += 1
n5 = r
put(s5, r, 1, "평가 시정촌 수", font=f_bold, fill=fill_avg, align=left)
for (h, e), c in cp.items():
    put(s5, r, c, int(S10.loc[e, COL[h][0]]), font=f_bold, fill=fill_avg)
for h, wc in (("LS", w5ls), ("LQ", w5lq)):
    cols = [c for (hh, _), c in cp.items() if hh == h]
    put(s5, r, wc, f"=SUM({get_column_letter(min(cols))}{r}:{get_column_letter(max(cols))}{r})", font=f_bold, fill=fill_avg)
put(s5, r, d5ls, "", fill=fill_avg); put(s5, r, d5lq, "", fill=fill_avg)
r += 1
put(s5, r, 1, "양성 / 음성", fill=fill_avg, align=left)
for (h, e), c in cp.items():
    put(s5, r, c, f"{int(S10.loc[e, COL[h][1]])} / {int(S10.loc[e, COL[h][2]])}", fill=fill_avg)
for h, wc in (("LS", w5ls), ("LQ", w5lq)):
    put(s5, r, wc, f"{sum(int(S10.loc[e, COL[h][1]]) for e in ev5[h])} / {sum(int(S10.loc[e, COL[h][2]]) for e in ev5[h])}",
        fill=fill_avg)
put(s5, r, d5ls, "", fill=fill_avg); put(s5, r, d5lq, "", fill=fill_avg)
r += 1
lam_rows = {}
for lam, _ in LAMS:
    lam_rows[lam] = r
    r += 1
ref = lam_rows["10"]
for lam, _ in LAMS:
    rr = lam_rows[lam]
    is_final = lam == "10"
    fill = fill_trace if is_final else None
    put(s5, rr, 1, f"{lam}" + (" (최종)" if is_final else ""), fill=fill, font=f_bold if is_final else f_body)
    for (h, e), c in cp.items():
        put(s5, rr, c, float(RES5[lam].loc[e, COL[h][4]]), fmt=NUM, fill=fill)
    for h, wc in (("LS", w5ls), ("LQ", w5lq)):
        cols = [c for (hh, _), c in cp.items() if hh == h]
        a, b = get_column_letter(min(cols)), get_column_letter(max(cols))
        put(s5, rr, wc, f"=SUMPRODUCT(${a}${n5}:${b}${n5},{a}{rr}:{b}{rr})/SUM(${a}${n5}:${b}${n5})",
            fmt=NUM, font=f_bold, fill=fill or fill_avg)
    for wc, dc in ((w5ls, d5ls), (w5lq, d5lq)):
        L = get_column_letter(wc)
        put(s5, rr, dc, f"={L}{rr}-{L}${ref}", fmt='+0.000;-0.000;0.000', fill=fill)
text(s5, r, "λ_γ = 10 행은 RQ1 표 2·RQ4 표 1의 AdminDER(전체)와 같은 결과.", f_note, span=17)
r += 2

# 표 2: λ별 배율(폴드 범위), 표 3: 폴드별 γ 원값
text(s5, r, "표 2. λ_γ별 피해 채널 배율 exp(γ) — 9개 LOEO 폴드의 최소~최대", f_h2, span=17)
r += 1
header(s5, r, ["재해 · 채널", "λ_γ = 0.1\n최소", "λ_γ = 0.1\n최대", "λ_γ = 1\n최소", "λ_γ = 1\n최대",
               "λ_γ = 10 (최종)\n최소", "λ_γ = 10 (최종)\n최대"])
r += 1
t2_rows = [(h, k) for h in ("LS", "LQ") for k in KOR]
t3_first = r + len(t2_rows) + 4  # 표 3 첫 데이터 행
lam_block = {lam: (t3_first + i * len(folds), t3_first + (i + 1) * len(folds) - 1) for i, (lam, _) in enumerate(LAMS)}
for h, k in t2_rows:
    col = get_column_letter(3 + (0 if h == "LS" else 6) + KOR.index(k))  # 표 3: C~H 산사태, I~N 액상화
    put(s5, r, 1, f"{HZ[h]} · {k}", align=left, font=f_bold)
    for i, (lam, _) in enumerate(LAMS):
        a, b = lam_block[lam]
        fill = fill_trace if lam == "10" else None
        put(s5, r, 2 + 2 * i, f"=EXP(MIN({col}{a}:{col}{b}))", fmt=NUM, fill=fill)
        put(s5, r, 3 + 2 * i, f"=EXP(MAX({col}{a}:{col}{b}))", fmt=NUM, fill=fill)
    r += 1
text(s5, r, "λ_γ가 작을수록 γ를 0으로 당기는 힘이 약해 배율이 커짐. AUC(표 1)보다 배율(RQ3의 해석)이 λ_γ에 훨씬 민감함.", f_note, span=17)
r += 2
text(s5, r, "표 3. 폴드별 γ 원값 (표 2의 근거)", f_h2, span=17)
r += 1
header(s5, r, ["λ_γ", "학습에서 뺀 지진"] + [f"산사태 γ\n{k}" for k in KOR] + [f"액상화 γ\n{k}" for k in KOR])
r += 1
assert r == t3_first, (r, t3_first)
for lam, _ in LAMS:
    for ev in folds:
        put(s5, r, 1, lam, fill=fill_trace if lam == "10" else None)
        put(s5, r, 2, ev, align=left)
        for i, k in enumerate(KOR):
            put(s5, r, 3 + i, GAM[lam][(ev, "LS", k)], fmt=NUM)
            put(s5, r, 9 + i, GAM[lam][(ev, "LQ", k)], fmt=NUM)
        r += 1
r += 1

# 표 4: prior (a, b) — 최종 설정에서 학습되는 값
text(s5, r, "표 4. prior 보정 파라미터 — 최종 설정에서 학습되는 값 (λ_γ = 10, 폴드별)", f_h2, span=17)
r += 1
header(s5, r, ["학습에서 뺀 지진", "산사태 a", "산사태 b", "산사태 κ\n(산지 비율 계수)", "액상화 a", "액상화 b\n(범위 [−20, 20])"])
r += 1
pf, pl = r, r + len(folds) - 1
for ev in folds:
    g = FOLD[FOLD.fold == ev]
    val = lambda grp, lab: float(g[(g.group == grp) & (g.label == lab)].value.iloc[0])
    put(s5, r, 1, ev, align=left)
    put(s5, r, 2, val("a", "LS"), fmt="0.0"); put(s5, r, 3, val("b", "LS"), fmt="0.0")
    put(s5, r, 4, val("kappa", "LS"), fmt="+0.000;-0.000;0.000")
    put(s5, r, 5, val("a", "LQ"), fmt="0.0"); put(s5, r, 6, val("b", "LQ"), fmt=NUM)
    r += 1
put(s5, r, 1, "최소 ~ 최대", font=f_bold, fill=fill_avg, align=left)
for c in (2, 3, 5):
    put(s5, r, c, "고정", fill=fill_avg)
put(s5, r, 4, f'=TEXT(MIN(D{pf}:D{pl}),"+0.000;-0.000")&" ~ "&TEXT(MAX(D{pf}:D{pl}),"+0.000;-0.000")', fill=fill_avg)
put(s5, r, 6, f'=TEXT(MIN(F{pf}:F{pl}),"0.000")&" ~ "&TEXT(MAX(F{pf}:F{pl}),"0.000")', fill=fill_avg)
r += 1
text(s5, r, "최종 설정은 a = 1, 산사태 b = 0을 유도식대로 고정하고 액상화 b만 학습. 학습된 액상화 b가 범위 [−20, 20]의 한참 안쪽이라 '자유 vs 범위 제약'은 결과를 바꾸지 않음.",
     f_note, span=17)
s5.row_dimensions[r].height = 28
r += 2

text(s5, r, "교수님께 여쭐 것", f_h2, span=17)
r += 1
for qtext in [
    "1. 논리구조의 '(a, b) 자유 / 범위 제약' 항목은 최종 설정과 맞지 않음(표 4). a도 학습하게 푸는 실험으로 바꿀지, 항목을 뺄지.",
    "2. λ_γ = 10은 9월 초 옛 모델(면적 prior·판독 범위·LOEO 도입 전)에서 {0.1, 1, 10} 중 AUC가 가장 높아서 고른 값. "
    "이 표는 최종 설정에서 λ_γ만 바꿔 다시 돌린 결과이며, 여기서도 산사태는 10이 가장 높고 액상화는 거의 같음. "
    "평가 성능으로 고른 것이라 논리구조의 '학습 이벤트 내부 LOEO' 또는 '사전 고정'에 해당하지 않음. "
    "중첩 LOEO(평가 지진마다 나머지 8개 안에서 λ 선택)를 돌릴지, 이 민감도 표로 갈음할지.",
    "3. AUC는 산사태가 λ_γ에 따라 0.852 → 0.905로 오르고 액상화는 거의 같지만, 배율(표 2)은 λ_γ에 따라 크게 달라짐 — RQ3 서술과 함께 정해야 함.",
]:
    c = text(s5, r, qtext, span=17)
    c.fill = fill_q
    s5.row_dimensions[r].height = 30
    r += 1
r += 1
text(s5, r, "출처", f_h2, span=17)
r += 1
for line in [
    "λ_γ = 0.1, 1: pilotA/outputs/holdout_summary_rq5l0.1_*.csv, holdout_summary_rq5l1_*.csv, outputs/rq5/gamma_lam0.1.csv · gamma_lam1.csv, 요약 outputs/rq5/rq5_lambda_auc.csv (2026-11-13 실행).",
    "λ_γ = 10: outputs/holdout_summary_rq4nl_full_*.csv, 폴드별 파라미터 outputs/언니전달_액상화J_설정/03_폴드별_전체파라미터_nolabels.csv.",
    "2026-09-02의 λ 실험(outputs/experiments)은 면적 prior·판독 범위·LOEO 이전 모델이라 여기에 쓰지 않음.",
]:
    text(s5, r, line, f_note, span=17)
    r += 1
for i, w in enumerate([18, 22] + [12] * 15, 1):
    s5.column_dimensions[get_column_letter(i)].width = w
s5.sheet_view.showGridLines = False

# 교수님께 드리는 엑셀은 표만: 시트 끝의 '교수님께 여쭐 것'·'알려드릴 것'·'출처' 구역을 지운다(질문은 슬랙으로 따로).
for s in wb.worksheets:
    start = next((row for row in range(1, s.max_row + 1)
                  if isinstance(s.cell(row, 1).value, str) and s.cell(row, 1).value.startswith("교수님께 여쭐 것")), None)
    if start is None:
        continue
    for m in [m for m in s.merged_cells.ranges if m.min_row >= start]:
        s.unmerge_cells(str(m))
    s.delete_rows(start - 1, s.max_row - start + 2)  # 바로 위 빈 줄까지

wb.save(OUT)
print("saved", OUT, {k: round(v, 6) if not np.isnan(v) else None for k, v in LQMAX.items()})
