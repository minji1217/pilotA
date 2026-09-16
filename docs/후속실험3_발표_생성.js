const pptxgen = require("pptxgenjs");

/* ── 팔레트: 주제에서 나온 색 ─────────────────────────────
   LS(산사태)=테라코타(흙), LQ(액상화)=틸(물). 두 hazard를 끝까지 이 색으로만 부른다. */
const INK   = "1C2A33";
const INK2  = "55636E";
const INK3  = "8A9BA8";
const BG    = "FFFFFF";
const BG2   = "F1F5F7";
const LS    = "B85042";
const LQ    = "1C7293";
const PRIOR = "A8B4BD";
const WARN  = "C9772F";
const GOOD  = "2C7A5A";

const KR = "맑은 고딕";
const NUM = "Calibri";
const W = 13.333, H = 7.5, M = 0.62;

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE";
pres.author = "Pilot A";
pres.title = "후속실험 3";

/* ── 헬퍼 ───────────────────────────────────────────── */
const slideBase = dark => { const s = pres.addSlide(); s.background = { color: dark ? INK : BG }; return s; };

function head(s, kicker, title, dark) {
  if (kicker) s.addText(kicker, { x: M, y: 0.44, w: 8.5, h: 0.26, isTextBox: true, margin: 0,
    fontFace: NUM, fontSize: 11, bold: true, charSpacing: 2, color: INK3 });
  s.addText(title, { x: M, y: kicker ? 0.76 : 0.6, w: W - 2 * M, h: 0.95, isTextBox: true, margin: 0,
    fontFace: KR, fontSize: 29, bold: true, color: dark ? BG : INK, valign: "top", lineSpacing: 35 });
}

const card = (s, o) => s.addShape(pres.ShapeType.roundRect, {
  x: o.x, y: o.y, w: o.w, h: o.h, rectRadius: 0.06,
  fill: { color: o.fill || BG2 }, line: { color: o.fill || BG2, width: 0 } });

function note(s, x, y, w, h, title, body, color) {
  card(s, { x, y, w, h, fill: color === LS ? "FBF1EE" : color === LQ ? "EDF4F7"
            : color === GOOD ? "EAF4EE" : BG2 });
  s.addText(title, { x: x + 0.3, y: y + 0.2, w: w - 0.6, h: 0.34, isTextBox: true, margin: 0,
    fontFace: KR, fontSize: 14.5, bold: true, color: color || INK });
  s.addText(body, { x: x + 0.3, y: y + 0.58, w: w - 0.6, h: h - 0.78, isTextBox: true, margin: 0,
    fontFace: KR, fontSize: 12, color: INK2, lineSpacing: 17 });
}

const chartFrame = () => ({
  showLegend: false,
  catAxisLabelColor: INK2, valAxisLabelColor: INK3,
  catAxisLabelFontFace: KR, valAxisLabelFontFace: NUM,
  catAxisLabelFontSize: 9, valAxisLabelFontSize: 9,
  valGridLine: { color: "E3E9EC", size: 1 }, catGridLine: { style: "none" },
  catAxisLineShow: false, valAxisLineShow: false, showTitle: false,
  dataLabelFontFace: NUM, dataLabelFontSize: 9, dataLabelColor: INK2,
});

/* ── 데이터 ─────────────────────────────────────────── */
const NAMES = ["1 3번 b4","2 3번 b10","3 6번 b10","4 3번 자연혼재","5 6번 자연혼재",
  "A fixed","B tied","C bounded","D free","E c 작게","F c 크게",
  "G LQ c=0.5","H LQ c=0.75","I LQ c 학습","J b만 학습"];
const GAIN_LS = [-0.0853,-0.0352,-0.0385,-0.0385,-0.0377,
  -0.0243,-0.0354,-0.0157,-0.0286,-0.0532,0.0005,-0.0204,-0.0230,-0.0200,-0.0384];
const MSE_LS = [0.1525,0.1498,0.1470,0.1275,0.1242,
  0.3683,0.1409,0.1148,0.1555,0.1429,0.7068,0.3685,0.3685,0.3684,0.1469];

/* ══════════ 1. 표지 ══════════ */
{
  const s = slideBase(true);
  s.addText("PILOT A · 후속실험 3", { x: M, y: 1.7, w: 10, h: 0.35, isTextBox: true, margin: 0,
    fontFace: NUM, fontSize: 13, bold: true, charSpacing: 3, color: INK3 });
  s.addText("평가 집합을 고치니\n결론이 뒤집혔다", { x: M, y: 2.2, w: 11.4, h: 2.0, isTextBox: true, margin: 0,
    fontFace: KR, fontSize: 42, bold: true, color: BG, lineSpacing: 54 });
  s.addText("LS 정답의 69%가 평가에서 빠져 있었다. 되돌리자 양성률이 84%에서 25%로 내려가면서,\n“잘 맞는다”던 조건이 사실은 확률을 0.44만큼 과대추정하고 있었던 것으로 드러났다.", {
    x: M, y: 4.4, w: 11.4, h: 0.8, isTextBox: true, margin: 0,
    fontFace: KR, fontSize: 14.5, color: "AFC0CB", lineSpacing: 22 });
  [["15","실험 조건"],["418","LS 평가 행"],["32,865","비교 쌍"],["9","이벤트"]].forEach(([v,l],i) => {
    const x = M + i * 2.2;
    s.addText(v, { x, y: 5.5, w: 2.0, h: 0.68, isTextBox: true, margin: 0,
      fontFace: NUM, fontSize: 30, bold: true, color: i === 0 ? LS : BG });
    s.addText(l, { x, y: 6.16, w: 2.0, h: 0.3, isTextBox: true, margin: 0,
      fontFace: KR, fontSize: 11, color: INK3 });
  });
  s.addNotes("핵심은 평가 집합이 편향돼 있었고, 그걸 고치니 이전 결론 둘이 뒤집혔다는 것.");
}

/* ══════════ 2. 세 번의 수정 ══════════ */
{
  const s = slideBase(false);
  head(s, "요약", "결과를 말하기 전에 — 세 가지를 고쳐야 했다", false);
  const rows = [
    ["기준선", "원값 prior → 자기 prior",
     "면적 항 조건의 prior는 z = a·log p̄ + b + c·log k 라 원값과 순위가 다르다", INK3],
    ["LS GT의 NA", "제외 → 0으로 포함",
     "LQ는 NA를 0으로 세는데 LS만 뺐다. 그런데 GT 439행 중 304행(69%)이 NA였다", LS],
    ["중심화", "이름 → 규칙",
     "-ctr 이름이 붙은 조건만 중심화해서 B·C·D·J는 b를 학습하는데도 빠져 있었다", LQ],
  ];
  rows.forEach(([t, w2, d, c], i) => {
    const y = 1.95 + i * 1.0;
    s.addShape(pres.ShapeType.ellipse, { x: M, y: y + 0.12, w: 0.4, h: 0.4, fill: { color: c } });
    s.addText(String(i + 1), { x: M, y: y + 0.17, w: 0.4, h: 0.3, isTextBox: true, margin: 0,
      align: "center", fontFace: NUM, fontSize: 14, bold: true, color: "FFFFFF" });
    s.addText(t, { x: M + 0.6, y: y + 0.04, w: 2.1, h: 0.34, isTextBox: true, margin: 0,
      fontFace: KR, fontSize: 15, bold: true, color: INK });
    s.addText(w2, { x: M + 2.75, y: y + 0.04, w: 3.3, h: 0.34, isTextBox: true, margin: 0,
      fontFace: KR, fontSize: 14, color: c });
    s.addText(d, { x: M + 0.6, y: y + 0.4, w: 11.4, h: 0.34, isTextBox: true, margin: 0,
      fontFace: KR, fontSize: 12, color: INK2 });
  });

  note(s, M, 5.15, 12.1, 1.75, "⚠ 이 중 (2)가 이전 결론 두 개를 뒤집었다",
    "“A fixed(유도식)가 LS 눈금이 완벽하다”(편향 +0.006)  →  정반대. 편향 +0.436, MSE 0.3683.\n" +
    "“b를 학습하면 LS 눈금이 무너진다”(편향 −0.27)  →  반대. C bounded 편향 +0.009, MSE 0.1148.\n" +
    "둘 다 양성률 84%짜리 집합에서 잰 값이었다. 음성이 될 행이 대부분 빠져 있어서 확률을 크게 부풀리는 모형이 “잘 맞는 모형”으로 보였다.", LS);
  s.addNotes("(2)가 이번 개정의 핵심. 나머지는 그것을 제대로 보기 위한 준비.");
}

/* ══════════ 3. 평가 집합이 어떻게 바뀌었나 ══════════ */
{
  const s = slideBase(false);
  head(s, "01", "LS 정답의 69%가 빠져 있었다", false);
  s.addText("LS와 LQ가 서로 다른 NA 규칙으로 돌고 있었다. LQ의 jshis_flag는 NA를 0으로 세는데 LS는 평가에서 뺐다.", {
    x: M, y: 1.78, w: 11.6, h: 0.32, isTextBox: true, margin: 0, fontFace: KR, fontSize: 13, color: INK2 });

  s.addChart(pres.ChartType.bar, [
    { name: "고치기 전", labels: ["LS 평가 행", "양성률 (%)", "AUC 정의 이벤트"], values: [125, 84.0, 5] },
    { name: "고친 뒤",   labels: ["LS 평가 행", "양성률 (%)", "AUC 정의 이벤트"], values: [418, 25.1, 9] },
  ], {
    x: M, y: 2.3, w: 7.0, h: 4.2, barDir: "col", barGrouping: "clustered", barGapWidthPct: 45,
    chartColors: [PRIOR, LS], ...chartFrame(), showLegend: true, legendPos: "t",
    legendFontFace: KR, legendFontSize: 11, legendColor: INK2,
    showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: "0.#",
    valAxisMinVal: 0, valAxisMaxVal: 450, catAxisLabelFontSize: 11,
  });
  s.addText("세 지표를 한 축에 놓았다 — 행 수·퍼센트·개수라 크기만 비교한다", {
    x: M, y: 6.58, w: 7.0, h: 0.3, isTextBox: true, margin: 0, align: "center",
    fontFace: KR, fontSize: 10.5, color: INK3 });

  note(s, 7.9, 2.3, 4.8, 2.1, "GT 439행 중 304행이 NA",
    "ls_flag 이벤트 6개: 1=64, 0=15, NA=178\nls_area_ha 이벤트 3개: >0=49, =0=7, NA=126\n\n" +
    "기록이 없다는 것은 그 시정촌에서 산사태가 확인되지 않았다는 뜻이므로 0으로 센다.", LS);
  note(s, 7.9, 4.6, 4.8, 2.1, "무엇이 달라지나",
    "MSE 기저확률 0.1344 → 0.1881\n비교 쌍 2,100 → 32,865 (16배)\n\n" +
    "불확실성이 크게 줄어 작은 차이도 판별할 수 있게 됐다.", LQ);
}

/* ══════════ 4. 무엇을 돌렸나 ══════════ */
{
  const s = slideBase(false);
  head(s, "02", "무엇을 돌렸나", false);
  s.addText("세 갈래 모두 같은 데이터·같은 seed. 조건마다 브랜치가 다르고, 면적 항은 prior.py / loader.py 자체가 다르다.\nGT는 학습에 전혀 쓰지 않는다 — 평가 전용이다.", {
    x: M, y: 1.78, w: 11.6, h: 0.6, isTextBox: true, margin: 0, fontFace: KR, fontSize: 13, color: INK2, lineSpacing: 19 });

  s.addTable([
    ["평가 집합", "행", "양성률", "MSE 기저확률"].map(t => ({ text: t, options: { bold: true, color: INK, fill: { color: BG2 } } })),
    ["LS (기존 GT)", "418", "25.1%", "0.1881"],
    ["LS (자연+혼재)", "398", "19.3%", "0.1560"],
    ["LQ", "229", "47.6%", "0.2494"],
  ].map(r => r.map((c, i) => typeof c === "string"
      ? { text: c, options: { align: i ? "right" : "left", fontFace: i ? NUM : KR } } : c)), {
    x: M, y: 2.6, w: 5.6, colW: [2.0, 1.1, 1.2, 1.3], rowH: 0.44,
    fontFace: KR, fontSize: 12, color: INK2, valign: "middle",
    border: { type: "solid", color: "E3E9EC", pt: 1 }, fill: { color: BG },
  });

  const groups = [
    ["②", "교수님 피드백 — b 범위", "3개. b 상한을 4 / 10으로 넓혀 안쪽에서 멈추는지", LS],
    ["③", "자연+혼재 GT 재평가", "2개. 학습은 그대로 두고 LS 정답만 좁힌다", WARN],
    ["④", "면적 항", "10개. z = a·log p̄ + b + c·log k 의 a·b·c를 어떻게 다룰지", LQ],
  ];
  groups.forEach(([n, t, d, c], i) => {
    const y = 4.7 + i * 0.82;
    s.addShape(pres.ShapeType.ellipse, { x: M, y: y + 0.06, w: 0.4, h: 0.4, fill: { color: c } });
    s.addText(n, { x: M, y: y + 0.11, w: 0.4, h: 0.3, isTextBox: true, margin: 0,
      align: "center", fontFace: KR, fontSize: 13, bold: true, color: "FFFFFF" });
    s.addText(t, { x: M + 0.6, y: y, w: 4.4, h: 0.32, isTextBox: true, margin: 0,
      fontFace: KR, fontSize: 14, bold: true, color: INK });
    s.addText(d, { x: M + 0.6, y: y + 0.32, w: 11.4, h: 0.32, isTextBox: true, margin: 0,
      fontFace: KR, fontSize: 11.5, color: INK2 });
  });

  note(s, 6.6, 2.6, 6.1, 1.76, "모두 lam_gamma = 10 · 3000 epoch · seed 0",
    "면적 항 10개 조건 모두 lam_gamma=10이 최선이었다.\n" +
    "회귀·likelihood 파라미터 44개는 모든 조건에서 학습한다. 표의 ‘학습’은 prior의 a·b·c 중 학습 개수다.", INK3);
}

/* ══════════ 4-2. 전체 결과 한 장 — 자기 prior vs posterior ══════════ */
const NL = "\n";   // 줄바꿈을 문자열에 직접 넣으면 소스가 깨져서 상수로 둔다
const ZP_LS   = [0.8778,0.8778,0.8778,0.9023,0.9023,0.8850,0.8850,0.8969,0.8776,0.8967,0.8373,0.8850,0.8850,0.8850,0.8850];
const POST_LS = [0.7925,0.8426,0.8405,0.8638,0.8646,0.8607,0.8496,0.8812,0.8490,0.8435,0.8379,0.8646,0.8620,0.8650,0.8466];
const ZP_LQ   = [0.7154,0.7154,0.8372,0.7154,0.8372,0.7698,0.7698,0.7709,0.7784,0.7570,0.7687,0.7570,0.7725,0.7547,0.7698];
const POST_LQ = [0.7504,0.7663,0.7753,0.7663,0.7753,0.7812,0.7871,0.7813,0.7814,0.7914,0.7681,0.7905,0.7955,0.7732,0.8100];

function pairSlide(kicker, title, dek, zp, post, col, capt, noteT, noteB) {
  const s = slideBase(false);
  head(s, kicker, title, false);
  s.addText(dek, { x: M, y: 1.78, w: 11.6, h: 0.34, isTextBox: true, margin: 0,
    fontFace: KR, fontSize: 13, color: INK2 });
  s.addChart(pres.ChartType.bar, [
    { name: "자기 prior", labels: NAMES, values: zp },
    { name: "posterior",  labels: NAMES, values: post },
  ], {
    x: M, y: 2.2, w: 8.0, h: 4.6, barDir: "bar", barGrouping: "clustered", barGapWidthPct: 25,
    chartColors: [PRIOR, col], ...chartFrame(), showLegend: true, legendPos: "t",
    legendFontFace: KR, legendFontSize: 11, legendColor: INK2,
    showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: "0.000",
    valAxisMinVal: 0.5, valAxisMaxVal: 1.0, valAxisLabelFormatCode: "0.0",
  });
  s.addText(capt, { x: M, y: 6.85, w: 8.0, h: 0.3, isTextBox: true, margin: 0, align: "center",
    fontFace: KR, fontSize: 10.5, color: INK3 });
  note(s, 8.85, 2.2, 3.85, 4.6, noteT, noteB, col);
}

pairSlide("03", "전체 결과 한 장 — 산사태 LS",
  "회색이 자기 prior 단독, 색이 posterior다. 색 막대가 회색보다 짧으면 피해 데이터가 오히려 깎았다는 뜻이다.",
  ZP_LS, POST_LS, LS, "가중평균 AUC · 가로축은 0.5(무작위)에서 시작",
  "15개 중 14개가 짧다",
  "posterior가 자기 prior를 넘은 것은 F 하나뿐이고 그마저 +0.0005다." + NL + NL +
  "4·5번은 자연+혼재 GT라 prior 기준선이 0.878 → 0.902로 함께 올라간다." + NL + NL +
  "비교 쌍이 32,865개로 16배 늘었는데도 방향이 바뀌지 않았다.");

pairSlide("04", "전체 결과 한 장 — 액상화 LQ",
  "같은 방식으로 LQ를 본다. 이쪽은 방향이 반대다.",
  ZP_LQ, POST_LQ, LQ, "가중평균 AUC · 가로축은 0.5(무작위)에서 시작",
  "대부분 posterior가 더 길다",
  "LQ에서는 13개 조건이 자기 prior를 넘는다(+0.003 ~ +0.040). J가 +0.040으로 1위다." + NL + NL +
  "예외는 3·5번(LQ 최대집계)과 F다. 3·5번은 prior가 0.837로 가장 좋은데 posterior가 0.775에 그쳐 −0.062로 가장 크게 깎는다." + NL + NL +
  "좋아진 prior를 모델이 오히려 망가뜨린다.");

/* ══════════ 5. LS 보탠 양 ══════════ */
{
  const s = slideBase(false);
  head(s, "05", "피해 데이터가 LS에 보탠 양", false);
  s.addText("posterior AUC − 자기 prior AUC (가중평균). 0보다 커야 피해 데이터가 보탠 것이 있다.", {
    x: M, y: 1.78, w: 11.6, h: 0.32, isTextBox: true, margin: 0, fontFace: KR, fontSize: 13, color: INK2 });

  s.addChart(pres.ChartType.bar, [{ name: "LS 보탠 양", labels: NAMES, values: GAIN_LS }], {
    x: M, y: 2.2, w: 7.9, h: 4.6, barDir: "bar", barGapWidthPct: 40,
    chartColors: [LS], ...chartFrame(),
    showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: "+0.000;-0.000",
    valAxisMinVal: -0.10, valAxisMaxVal: 0.015, valAxisLabelFormatCode: "0.00",
  });

  note(s, 8.75, 2.2, 3.95, 2.3, "15개 중 14개가 음수",
    "유일한 양수 F(+0.0005)는 LS MSE 0.7068, 편향 +0.715로 다른 모든 지표에서 최악이다.\n\n" +
    "비교 쌍이 32,865개로 16배 늘었는데도 방향이 바뀌지 않는다.", LS);
  note(s, 8.75, 4.7, 3.95, 2.1, "LQ는 반대다",
    "LQ에서는 대부분 보탠다(+0.003 ~ +0.040).\n\n" +
    "지금 모델에서 피해 데이터가 LS에 보태는 것이 없다는 것이 이번 실험의 가장 큰 발견이다.", LQ);
  s.addNotes("부트스트랩: A −0.017 [−0.039,+0.007], C +0.011 [−0.011,+0.035], E −0.039 [−0.064,−0.012].");
}

/* ══════════ 6. c = 1 은 확률을 부풀린다 ══════════ */
{
  const s = slideBase(false);
  head(s, "06", "c = 1 은 확률을 부풀린다 — 두 hazard 모두", false);
  s.addText("USGS 값 p̄는 칸 면적 중 덮일 비율이다. 칸이 독립이면 λ = p̄ × k 이고 순위가 같은 log λ 를 쓴다.\n그래서 c = 1이 유도식 그대로다 — 그런데 그 독립 가정이 맞지 않는다.", {
    x: M, y: 1.78, w: 11.6, h: 0.6, isTextBox: true, margin: 0, fontFace: KR, fontSize: 13, color: INK2, lineSpacing: 19 });

  s.addChart(pres.ChartType.bar, [
    { name: "산사태 LS", labels: ["c = 0.5", "c = 1.0", "c = 2.0"], values: [-0.097, 0.436, 0.715] },
    { name: "액상화 LQ", labels: ["c = 0.5", "c = 1.0", "c = 2.0"], values: [-0.103, 0.256, 0.501] },
  ], {
    x: M, y: 2.5, w: 7.0, h: 4.0, barDir: "col", barGrouping: "clustered", barGapWidthPct: 45,
    chartColors: [LS, LQ], ...chartFrame(), showLegend: true, legendPos: "t",
    legendFontFace: KR, legendFontSize: 11, legendColor: INK2,
    showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: "+0.000;-0.000",
    valAxisMinVal: -0.25, valAxisMaxVal: 0.85, valAxisLabelFormatCode: "0.0", catAxisLabelFontSize: 12,
  });
  s.addText("예측 편향 = 평균 예측확률 − 실제 양성률 (LS 0.251 / LQ 0.476)", {
    x: M, y: 6.58, w: 7.0, h: 0.3, isTextBox: true, margin: 0, align: "center",
    fontFace: KR, fontSize: 10.5, color: INK3 });

  note(s, 7.9, 2.5, 4.8, 1.95, "이전 판이 왜 반대로 보였나",
    "평가 집합이 양성 84%였다. 그러면 “거의 다 양성이라 찍는 모형”이 잘 맞는 것처럼 보인다.\n" +
    "실제 양성률이 0.251로 내려가자 A fixed의 평균 예측 0.687이 정체를 드러냈다.", LS);
  note(s, 7.9, 4.65, 4.8, 1.85, "LS의 최적 c도 0.5~1 사이다",
    "LQ와 같은 방향이다. 칸이 공간적으로 상관되어 1 − ∏(1−pᵢ)가 과대추정한다는 뜻이다.\n" +
    "“LS는 유도식 c=1이 맞다”는 이전 진단은 착시였다.", LQ);
}

/* ══════════ 7. b를 학습하면 교정된다 ══════════ */
{
  const s = slideBase(false);
  head(s, "07", "b를 학습하면 교정된다", false);
  s.addText("b는 z에 더해지는 상수라 hazard 안에서 순위를 바꾸지 않고 확률 수준만 옮긴다. 중심화까지 적용하니 제 역할을 한다.", {
    x: M, y: 1.78, w: 11.6, h: 0.32, isTextBox: true, margin: 0, fontFace: KR, fontSize: 13, color: INK2 });

  s.addChart(pres.ChartType.bar, [{ name: "LS MSE", labels: NAMES, values: MSE_LS }], {
    x: M, y: 2.2, w: 7.9, h: 4.6, barDir: "bar", barGapWidthPct: 40,
    chartColors: [LQ], ...chartFrame(),
    showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: "0.000",
    valAxisMinVal: 0, valAxisMaxVal: 0.78, valAxisLabelFormatCode: "0.0",
  });
  s.addText("LS MSE (낮을수록 좋음) — 기저확률 베이스라인 0.1881", {
    x: M, y: 6.85, w: 7.9, h: 0.3, isTextBox: true, margin: 0, align: "center",
    fontFace: KR, fontSize: 10.5, color: INK3 });

  note(s, 8.75, 2.2, 3.95, 2.35, "C bounded − A fixed (LS)",
    "AUC  +0.0282  [+0.013, +0.045]   유의\nMSE  −0.2534  [−0.294, −0.212]   유의\n\n" +
    "C는 기저확률(0.1881)을 넘는 유일한 면적 조건이고 편향은 +0.009다.", GOOD);
  note(s, 8.75, 4.75, 3.95, 2.05, "A·G·H·I가 0.37로 튄다",
    "넷 다 c_LS = 1 이고 b = 0 고정이다.\n" +
    "순위(AUC)는 나쁘지 않은데 확률 수준이 두 배 넘게 부풀려져 MSE가 무너진다.", LS);
}

/* ══════════ 8. 전체 결과 표 ══════════ */
{
  const s = slideBase(false);
  head(s, "08", "전체 결과 15개 조건", false);
  const rows = [
    ["1","3번 b4","a·b","—","—","0.7925","−0.085","0.1525","+0.063","0.7504","+0.035","0.2280"],
    ["2","3번 b10","a·b","—","—","0.8426","−0.035","0.1498","+0.084","0.7663","+0.051","0.2428"],
    ["3","6번 b10","a·b","—","—","0.8405","−0.037","0.1470","+0.081","0.7753","−0.062","0.2409"],
    ["4","3번 자연혼재","a·b","—","—","0.8638","−0.039","0.1275","+0.134","0.7663","+0.051","0.2428"],
    ["5","6번 자연혼재","a·b","—","—","0.8646","−0.038","0.1242","+0.131","0.7753","−0.062","0.2409"],
    ["A","fixed","0","1.00","1.00","0.8607","−0.024","0.3683","+0.436","0.7812","+0.011","0.2497"],
    ["B","tied","4","0.89","0.50","0.8496","−0.035","0.1409","+0.089","0.7871","+0.017","0.2530"],
    ["C","bounded","4","1.00","1.00","0.8812","−0.016","0.1148","+0.009","0.7813","+0.010","0.2507"],
    ["D","free","6","0.01","0.78","0.8490","−0.029","0.1555","+0.091","0.7814","+0.003","0.2411"],
    ["E","c 작게","0","0.50","0.50","0.8435","−0.053","0.1429","−0.097","0.7914","+0.034","0.1932"],
    ["F","c 크게","0","2.00","2.00","0.8379","+0.001","0.7068","+0.715","0.7681","−0.001","0.4896"],
    ["G","LQ c=0.5","0","1.00","0.50","0.8646","−0.020","0.3685","+0.437","0.7905","+0.034","0.1929"],
    ["H","LQ c=0.75","0","1.00","0.75","0.8620","−0.023","0.3685","+0.436","0.7955","+0.023","0.1868"],
    ["I","LQ c 학습","1","1.00","0.43","0.8650","−0.020","0.3684","+0.437","0.7732","+0.019","0.2155"],
    ["J","b만 학습","2","1.00","1.00","0.8466","−0.038","0.1469","+0.083","0.8100","+0.040","0.2217"],
  ];
  const hi = new Set(["C", "E", "J"]);
  const hdr = ["#","이름","학습","c_LS","c_LQ","LS AUC","LS 보탠양","LS MSE","LS 편향","LQ AUC","LQ 보탠양","LQ MSE"];
  s.addTable([
    hdr.map((h, i) => ({ text: h, options: { bold: true, color: INK, fill: { color: BG2 },
      align: i >= 2 ? "right" : "left", fontSize: 10 } })),
    ...rows.map(r => r.map((c, i) => ({
      text: c,
      options: { align: i >= 2 ? "right" : "left", fontFace: i >= 2 ? NUM : KR,
                 bold: hi.has(r[0]), color: hi.has(r[0]) ? INK : INK2,
                 fill: { color: hi.has(r[0]) ? "EAF4EE" : BG } },
    }))),
  ], {
    x: M, y: 1.95, w: 12.1, colW: [0.45, 1.5, 0.7, 0.75, 0.75, 1.15, 1.25, 1.1, 1.1, 1.15, 1.25, 1.1],
    rowH: 0.3, fontFace: KR, fontSize: 10, valign: "middle",
    border: { type: "solid", color: "E3E9EC", pt: 1 },
  });
  s.addText("‘보탠양’ = posterior AUC − 자기 prior AUC (가중평균).  기저확률 MSE: LS 0.1881(4·5번은 0.1560) / LQ 0.2494.  초록 = 아래 슬라이드의 세 후보.", {
    x: M, y: 6.85, w: 12.1, h: 0.3, isTextBox: true, margin: 0, fontFace: KR, fontSize: 10.5, color: INK3 });
}

/* ══════════ 9. ③ 자연+혼재 ══════════ */
{
  const s = slideBase(false);
  head(s, "09", "③ 자연+혼재는 여전히 유효하다", false);
  s.addText("USGS 산사태 사전모형이 설명하는 것은 자연사면의 붕괴인데, GT의 양성에는 성토·옹벽·법면 같은\n인공사면 붕괴가 섞여 있었다. 평가 집합을 고친 뒤에도 이 결론은 그대로다.", {
    x: M, y: 1.78, w: 11.6, h: 0.6, isTextBox: true, margin: 0, fontFace: KR, fontSize: 13, color: INK2, lineSpacing: 19 });

  s.addChart(pres.ChartType.bar, [
    { name: "자기 prior", labels: ["기존 GT (2번)", "자연+혼재 (4번)"], values: [0.8778, 0.9023] },
    { name: "posterior",  labels: ["기존 GT (2번)", "자연+혼재 (4번)"], values: [0.8426, 0.8638] },
  ], {
    x: M, y: 2.5, w: 6.4, h: 3.9, barDir: "col", barGrouping: "clustered", barGapWidthPct: 50,
    chartColors: [PRIOR, WARN], ...chartFrame(), showLegend: true, legendPos: "t",
    legendFontFace: KR, legendFontSize: 11, legendColor: INK2,
    showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: "0.000",
    valAxisMinVal: 0.80, valAxisMaxVal: 0.93, valAxisLabelFormatCode: "0.00", catAxisLabelFontSize: 12,
  });
  s.addText("LS AUC — 모델은 그대로, 정답만 바꿨을 때", {
    x: M, y: 6.48, w: 6.4, h: 0.3, isTextBox: true, margin: 0, align: "center",
    fontFace: KR, fontSize: 10.5, color: INK3 });

  note(s, 7.3, 2.5, 5.4, 2.0, "모델을 한 줄도 바꾸지 않았다",
    "그런데 자기 prior가 0.8778 → 0.9023으로 오른다. 원래 맞히고 있던 것을 그동안 틀렸다고 채점하고 있었다는 뜻이다.\n" +
    "posterior 0.8426 → 0.8638, MSE 0.1498 → 0.1275.", WARN);
  note(s, 7.3, 4.7, 5.4, 2.1, "⚠ 그런데 LQ 최대집계는 반대다",
    "LQ prior를 최대집계로 바꾸면 prior 자체의 AUC가 0.7154 → 0.8372로 크게 오른다.\n" +
    "그런데 posterior는 0.7753에 그친다 — 자기 prior보다 0.062 낮다. 좋아진 prior를 모델이 깎아먹는다.", LQ);
}

/* ══════════ 10. 어느 조건을 쓸 것인가 ══════════ */
{
  const s = slideBase(false);
  head(s, "10", "어느 조건을 쓸 것인가 — 트레이드오프다", false);
  s.addText("네 지표를 모두 통과하는 조건은 없다. LS 보탠양이 양수인 것이 F뿐이고 F는 나머지가 최악이기 때문이다.\n그 지표를 빼고 보면 셋이 갈린다.", {
    x: M, y: 1.78, w: 11.6, h: 0.6, isTextBox: true, margin: 0, fontFace: KR, fontSize: 13, color: INK2, lineSpacing: 19 });

  const cands = [
    ["C bounded", "순위가 중요할 때", [["LS AUC","0.8812",1],["LS MSE","0.1148",1],["LS 편향","+0.009",1],
      ["LQ AUC","0.7813",0],["LQ MSE","0.2507",-1],["LQ 편향","−0.214",0]], LQ],
    ["E c = 0.5", "확률 눈금이 중요할 때", [["LS AUC","0.8435",0],["LS MSE","0.1429",1],["LS 편향","−0.097",0],
      ["LQ AUC","0.7914",0],["LQ MSE","0.1932",1],["LQ 편향","−0.103",1]], GOOD],
    ["J b만 학습", "LQ가 중요할 때", [["LS AUC","0.8466",0],["LS MSE","0.1469",1],["LS 편향","+0.083",0],
      ["LQ AUC","0.8100",1],["LQ MSE","0.2217",1],["LQ 편향","−0.192",0]], LS],
  ];
  cands.forEach(([nm, use, metrics, col], i) => {
    const x = M + i * 4.1;
    card(s, { x, y: 2.6, w: 3.85, h: 4.0, fill: BG2 });
    s.addShape(pres.ShapeType.rect, { x: x + 0.3, y: 2.86, w: 0.16, h: 0.16, fill: { color: col } });
    s.addText(nm, { x: x + 0.56, y: 2.78, w: 3.0, h: 0.34, isTextBox: true, margin: 0,
      fontFace: KR, fontSize: 16, bold: true, color: INK });
    s.addText(use, { x: x + 0.3, y: 3.16, w: 3.25, h: 0.3, isTextBox: true, margin: 0,
      fontFace: KR, fontSize: 12, color: col });
    metrics.forEach(([k, v, good], j) => {
      const y = 3.6 + j * 0.45;
      s.addText(k, { x: x + 0.3, y, w: 1.52, h: 0.3, isTextBox: true, margin: 0,
        fontFace: KR, fontSize: 11.5, color: INK2 });
      s.addText(v, { x: x + 1.9, y, w: 1.65, h: 0.3, isTextBox: true, margin: 0, align: "right",
        fontFace: NUM, fontSize: 13, bold: good === 1,
        color: good === 1 ? GOOD : good === -1 ? LS : INK2 });
    });
  });
  s.addText("C는 LS AUC 1위에 눈금도 거의 완벽하지만 LQ MSE가 기저확률(0.2494)에 0.0013 차이로 미달한다.  E는 학습 파라미터 0개로 평균 MSE·최대 편향 모두 1위다.  J는 LQ AUC와 보탠양이 모두 1위다.", {
    x: M, y: 6.75, w: 12.1, h: 0.4, isTextBox: true, margin: 0, fontFace: KR, fontSize: 11, color: INK3 });
}

/* ══════════ 11. 한계와 다음 ══════════ */
{
  const s = slideBase(true);
  head(s, "11", "한계와 다음", true);
  const items = [
    ["LS에서 피해 데이터가 보태는 것이 없다", "15개 중 14개가 자기 prior보다 낮다. 왜 그런지가 다음 연구의 중심이어야 한다.", LS],
    ["c_LS도 1보다 낮춰야 한다", "E(c=0.5)의 편향 −0.097과 A(c=1)의 +0.436 사이에 최적값이 있다. c_LS × c_LQ를 0.5~1 구간에서 훑는 실험이 다음 순서다.", WARN],
    ["③과 ④를 결합하지 않았다", "면적 항 10개 조건은 전부 기존(all) GT로 돌았다.", WARN],
    ["LQ 최대집계 + 면적 항을 안 해봤다", "가장 좋은 LQ prior(0.8372)와 면적 항을 한 번도 같이 쓰지 않았다. 다만 λ = p̄·k 유도가 평균집계를 전제하므로 이론 정리가 먼저다.", LQ],
    ["LQ 평가는 229행뿐이다", "LS는 418행으로 늘었지만 LQ는 GT 시트가 덮는 범위가 그대로다.", INK3],
  ];
  items.forEach(([t, d, c], i) => {
    const y = 1.95 + i * 1.0;
    s.addShape(pres.ShapeType.ellipse, { x: M, y: y + 0.08, w: 0.22, h: 0.22, fill: { color: c } });
    s.addText(t, { x: M + 0.44, y, w: 11.6, h: 0.34, isTextBox: true, margin: 0,
      fontFace: KR, fontSize: 15, bold: true, color: BG });
    s.addText(d, { x: M + 0.44, y: y + 0.36, w: 11.6, h: 0.5, isTextBox: true, margin: 0,
      fontFace: KR, fontSize: 12, color: "AFC0CB", lineSpacing: 16 });
  });
  s.addText("재현:  python tools/build_dataset.py --area-from-usgs  →  python run_followup3.py --data-dir .", {
    x: M, y: 7.0, w: 11.6, h: 0.3, isTextBox: true, margin: 0, fontFace: NUM, fontSize: 11, color: INK3 });
}

pres.writeFile({ fileName: "후속실험3.pptx" }).then(f => console.log("생성:", f));
