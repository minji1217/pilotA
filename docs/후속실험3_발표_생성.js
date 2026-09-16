const pptxgen = require("pptxgenjs");

/* ── 팔레트: 주제에서 나온 색 ─────────────────────────────
   LS(산사태)=테라코타(흙), LQ(액상화)=틸(물). 두 hazard를 끝까지 이 색으로만 부른다. */
const INK   = "1C2A33";  // 딥 슬레이트
const INK2  = "55636E";
const INK3  = "8A9BA8";
const BG    = "FFFFFF";
const BG2   = "F1F5F7";
const LS    = "B85042";  // 테라코타
const LQ    = "1C7293";  // 틸
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

/* ── 공통 헬퍼 ───────────────────────────────────────── */
function slideBase(dark) {
  const s = pres.addSlide();
  s.background = { color: dark ? INK : BG };
  return s;
}

// 상단 제목 블록. 악센트 줄 없이 여백과 색만으로 위계를 만든다.
function head(s, kicker, title, dark) {
  if (kicker) {
    s.addText(kicker, {
      x: M, y: 0.44, w: 8.5, h: 0.26, isTextBox: true, margin: 0,
      fontFace: NUM, fontSize: 11, bold: true, charSpacing: 2,
      color: dark ? INK3 : INK3,
    });
  }
  s.addText(title, {
    x: M, y: kicker ? 0.76 : 0.6, w: W - 2 * M, h: 0.95, isTextBox: true, margin: 0,
    fontFace: KR, fontSize: 30, bold: true, color: dark ? BG : INK,
    valign: "top", lineSpacing: 36,
  });
}

// hazard 표식: 작은 정사각형 + 이름. 전 슬라이드 공통 모티프.
function hazardChip(s, x, y, which) {
  s.addShape(pres.ShapeType.rect, {
    x, y, w: 0.14, h: 0.14, fill: { color: which === "LS" ? LS : LQ },
  });
  s.addText(which === "LS" ? "산사태 LS" : "액상화 LQ", {
    x: x + 0.22, y: y - 0.06, w: 1.6, h: 0.26, isTextBox: true, margin: 0,
    fontFace: KR, fontSize: 11, bold: true, color: INK2,
  });
}

function card(s, o) {
  s.addShape(pres.ShapeType.roundRect, {
    x: o.x, y: o.y, w: o.w, h: o.h, rectRadius: 0.06,
    fill: { color: o.fill || BG2 },
    line: o.line ? { color: o.line, width: 1 } : { color: o.fill || BG2, width: 0 },
  });
}

function stat(s, x, y, w, value, label, color) {
  s.addText(value, {
    x, y, w, h: 0.78, isTextBox: true, margin: 0,
    fontFace: NUM, fontSize: 36, bold: true, color: color || INK,
  });
  s.addText(label, {
    x, y: y + 0.76, w, h: 0.5, isTextBox: true, margin: 0,
    fontFace: KR, fontSize: 12, color: INK2, lineSpacing: 16,
  });
}

function bullets(s, x, y, w, h, items, size) {
  s.addText(items.map((t, i) => ({
    text: t, options: { bullet: true, breakLine: i !== items.length - 1 },
  })), {
    x, y, w, h, isTextBox: true, margin: 0,
    fontFace: KR, fontSize: size || 14, color: INK2,
    paraSpaceAfter: 9, lineSpacing: 20,
  });
}

const chartFrame = () => ({
  showLegend: false,
  catAxisLabelColor: INK2, valAxisLabelColor: INK3,
  catAxisLabelFontFace: KR, valAxisLabelFontFace: NUM,
  catAxisLabelFontSize: 9, valAxisLabelFontSize: 9,
  valGridLine: { color: "E3E9EC", size: 1 },
  catGridLine: { style: "none" },
  catAxisLineShow: false, valAxisLineShow: false,
  showTitle: false,
  dataLabelFontFace: NUM, dataLabelFontSize: 9, dataLabelColor: INK2,
});

/* ══════════════════ 1. 표지 ══════════════════ */
{
  const s = slideBase(true);
  s.addText("PILOT A · 후속실험 3", {
    x: M, y: 1.75, w: 10, h: 0.35, isTextBox: true, margin: 0,
    fontFace: NUM, fontSize: 13, bold: true, charSpacing: 3, color: INK3,
  });
  s.addText("순위를 올린 것은 면적 항이고,\n피해 데이터는 LS에서 오히려 깎는다", {
    x: M, y: 2.25, w: 11.4, h: 2.0, isTextBox: true, margin: 0,
    fontFace: KR, fontSize: 40, bold: true, color: BG, lineSpacing: 52,
  });
  s.addText("b 범위 · 자연+혼재 GT · 면적 항 — 19개 조건을 9개 이벤트 418행 전체로", {
    x: M, y: 4.45, w: 11, h: 0.4, isTextBox: true, margin: 0,
    fontFace: KR, fontSize: 15, color: "AFC0CB",
  });
  const items = [["19", "실험 조건"], ["61", "학습 실행"], ["418", "모델 행"], ["9", "이벤트"]];
  items.forEach(([v, l], i) => {
    const x = M + i * 1.95;
    s.addText(v, { x, y: 5.4, w: 1.8, h: 0.68, isTextBox: true, margin: 0,
      fontFace: NUM, fontSize: 32, bold: true, color: i === 0 ? LS : BG });
    s.addText(l, { x, y: 6.06, w: 1.8, h: 0.3, isTextBox: true, margin: 0,
      fontFace: KR, fontSize: 11, color: INK3 });
  });
  s.addNotes("후속실험 3 전체 결과. 핵심은 기준선을 고치면 해석이 뒤집힌다는 것.");
}

/* ══════════════════ 2. 한 장 요약 ══════════════════ */
{
  const s = slideBase(false);
  head(s, "요약", "발견 세 가지", false);
  const rows = [
    ["1", "b를 학습하면 예외 없이 LS 눈금이 무너진다",
     "19개를 'b를 학습하는가'로 가르면 완전히 갈린다. 학습하는 13개는 전부 LS를 20~30%p 과소예측한다.\n학습 목표가 피해 데이터의 marginal likelihood이지 GT가 아니기 때문이다.", LS],
    ["2", "자유도를 주면 면적 항 자체를 버린다",
     "free 조건은 c_LS를 0.005까지 떨어뜨려 면적 항을 사실상 제거했고,\nprior 순위가 USGS 원값 수준(0.749)으로 돌아갔다. 순위를 올려 주던 바로 그 항을 버린 것이다.", WARN],
    ["3", "LS·LQ를 동시에 잡으려면 c를 hazard별로 나눠야 한다",
     "LS는 유도식 c=1에서 편향 +0.006으로 이미 맞는데 LQ는 같은 값에서 +0.256 과대예측한다.\nc_LS=1을 지키고 c_LQ만 0.5~0.75로 낮춘 조건이 둘 다 잡는다.", LQ],
  ];
  rows.forEach(([n, t, d, c], i) => {
    const y = 1.95 + i * 1.62;
    card(s, { x: M, y, w: W - 2 * M, h: 1.42 });
    s.addShape(pres.ShapeType.ellipse, { x: M + 0.3, y: y + 0.44, w: 0.48, h: 0.48, fill: { color: c } });
    s.addText(n, { x: M + 0.3, y: y + 0.5, w: 0.48, h: 0.36, isTextBox: true, margin: 0,
      align: "center", fontFace: NUM, fontSize: 17, bold: true, color: "FFFFFF" });
    s.addText(t, { x: M + 1.0, y: y + 0.24, w: 10.9, h: 0.42, isTextBox: true, margin: 0,
      fontFace: KR, fontSize: 17, bold: true, color: INK });
    s.addText(d, { x: M + 1.0, y: y + 0.68, w: 10.9, h: 0.66, isTextBox: true, margin: 0,
      fontFace: KR, fontSize: 12, color: INK2, lineSpacing: 17 });
  });
  s.addNotes("세 줄이 전부. 1번이 이번 실험의 중심 메시지.");
}

/* ══════════════════ 3. 기준선 정정 ══════════════════ */
{
  const s = slideBase(true);
  head(s, "정정", "먼저 — 기준선이 틀려 있었다", true);
  s.addText("처음 집계는 posterior를 USGS 원값 p̄와 비교했다. 이건 “USGS를 이겼나”만 답한다.\n면적 항 조건의 prior는  z = a·log p̄ + b + c·log k  이므로, “피해 데이터가 무엇을 보탰나”를\n재려면 그 z로 매긴 순위와 비교해야 한다.", {
    x: M, y: 1.92, w: 11.6, h: 1.0, isTextBox: true, margin: 0,
    fontFace: KR, fontSize: 14, color: "C3D0D8", lineSpacing: 22,
  });

  const cols = [
    ["USGS 원값  p̄", "USGS를 이겼나", "0.7486", "0.7485", INK3],
    ["자기 prior  log p̄ + log k", "피해 데이터가 보탰나", "0.8410", "0.8183", LQ],
  ];
  cols.forEach(([t, q, ls, lq, c], i) => {
    const x = M + i * 5.9;
    s.addShape(pres.ShapeType.roundRect, { x, y: 3.15, w: 5.5, h: 1.72, rectRadius: 0.06,
      fill: { color: i === 1 ? "24404E" : "26333C" } });
    s.addText(t, { x: x + 0.34, y: 3.36, w: 5.0, h: 0.34, isTextBox: true, margin: 0,
      fontFace: KR, fontSize: 14, bold: true, color: i === 1 ? "8FD0E8" : "AFC0CB" });
    s.addText(q, { x: x + 0.34, y: 3.68, w: 5.0, h: 0.3, isTextBox: true, margin: 0,
      fontFace: KR, fontSize: 11, color: INK3 });
    s.addText(ls, { x: x + 0.34, y: 4.06, w: 2.2, h: 0.6, isTextBox: true, margin: 0,
      fontFace: NUM, fontSize: 28, bold: true, color: i === 1 ? BG : "8A9BA8" });
    s.addText(lq, { x: x + 2.7, y: 4.06, w: 2.2, h: 0.6, isTextBox: true, margin: 0,
      fontFace: NUM, fontSize: 28, bold: true, color: i === 1 ? BG : "8A9BA8" });
    s.addText("LS", { x: x + 0.34, y: 4.62, w: 2.2, h: 0.24, isTextBox: true, margin: 0,
      fontFace: NUM, fontSize: 10, color: INK3 });
    s.addText("LQ", { x: x + 2.7, y: 4.62, w: 2.2, h: 0.24, isTextBox: true, margin: 0,
      fontFace: NUM, fontSize: 10, color: INK3 });
  });

  s.addText([
    { text: "이 하나로 승패가 뒤집힌다. ", options: { color: "C3D0D8" } },
    { text: "A fixed는 원값 기준 +0.091 승이지만 자기 prior 기준으로는 −0.001 패다.", options: { bold: true, color: BG } },
  ], { x: M, y: 5.25, w: 11.6, h: 0.44, isTextBox: true, margin: 0, fontFace: KR, fontSize: 15 });
  s.addText("AreaPrior.z() 의 주석은 이 용도를 적어 두었지만 to_eval_pred 가 한 번도 호출하지 않고 있었다.", {
    x: M, y: 5.78, w: 11.6, h: 0.36, isTextBox: true, margin: 0,
    fontFace: KR, fontSize: 12, color: INK3,
  });
  s.addNotes("이 슬라이드가 나머지 전부의 전제. 기준선을 바꾸면 이전 결론이 유지되지 않는다.");
}

/* ══════════════════ 4. 무엇을 돌렸나 ══════════════════ */
{
  const s = slideBase(false);
  head(s, "01", "무엇을 돌렸나", false);
  s.addText("세 갈래 모두 같은 데이터·같은 seed. 조건마다 브랜치가 다르고, 면적 항은 prior.py / loader.py 자체가 다르다.\nGT는 학습에 전혀 쓰지 않는다 — 평가 전용이다.", {
    x: M, y: 1.82, w: 11.6, h: 0.6, isTextBox: true, margin: 0,
    fontFace: KR, fontSize: 13, color: INK2, lineSpacing: 19,
  });

  card(s, { x: M, y: 2.62, w: 5.4, h: 1.5 });
  stat(s, M + 0.36, 2.82, 1.6, "418", "모델 입력 행\n439 → 419 → 418");
  stat(s, M + 2.1, 2.82, 1.6, "125", "LS 평가 행\n양성 105", LS);
  stat(s, M + 3.8, 2.82, 1.6, "229", "LQ 평가 행\n양성 109", LQ);

  const groups = [
    ["②", "교수님 피드백 — b 범위", "3개 조건. b 상한을 4 / 10으로 넓혀 안쪽에서 멈추는지 본다.", LS],
    ["③", "자연+혼재 GT 재평가", "2개 조건. 학습은 그대로 두고 LS 정답만 자연+혼재로 좁힌다.", WARN],
    ["④", "면적 항", "14개 조건. z = a·log p̄ + b + c·log k 의 a·b·c를 어떻게 다룰지.", LQ],
  ];
  groups.forEach(([n, t, d, c], i) => {
    const y = 4.35 + i * 0.94;
    s.addShape(pres.ShapeType.ellipse, { x: M, y: y + 0.12, w: 0.42, h: 0.42, fill: { color: c } });
    s.addText(n, { x: M, y: y + 0.17, w: 0.42, h: 0.32, isTextBox: true, margin: 0,
      align: "center", fontFace: KR, fontSize: 14, bold: true, color: "FFFFFF" });
    s.addText(t, { x: M + 0.62, y: y + 0.04, w: 5.0, h: 0.34, isTextBox: true, margin: 0,
      fontFace: KR, fontSize: 15, bold: true, color: INK });
    s.addText(d, { x: M + 0.62, y: y + 0.38, w: 11.0, h: 0.34, isTextBox: true, margin: 0,
      fontFace: KR, fontSize: 12, color: INK2 });
  });

  card(s, { x: 6.3, y: 2.62, w: 6.4, h: 1.5, fill: "FBF1EE" });
  s.addText("모두 lam_gamma = 10 · 3000 epoch · seed 0", {
    x: 6.66, y: 2.86, w: 5.8, h: 0.3, isTextBox: true, margin: 0,
    fontFace: KR, fontSize: 13, bold: true, color: LS,
  });
  s.addText("④는 lam 0 / 0.1 / 1 / 10을 모두 돌렸고, 비교는 10 기준이다.\n회귀·likelihood 파라미터 44개는 모든 조건에서 학습한다.", {
    x: 6.66, y: 3.2, w: 5.8, h: 0.7, isTextBox: true, margin: 0,
    fontFace: KR, fontSize: 12, color: INK2, lineSpacing: 17,
  });
}

/* ══════════════════ 5. 전체 결과 — LS 보탠 양 ══════════════════ */
{
  const s = slideBase(false);
  head(s, "02", "피해 데이터가 LS에 보탠 양", false);
  s.addText("posterior AUC − 자기 prior AUC. 0보다 커야 피해 데이터가 보탠 것이 있다.", {
    x: M, y: 1.78, w: 11.6, h: 0.32, isTextBox: true, margin: 0,
    fontFace: KR, fontSize: 13, color: INK2,
  });

  const labels = ["1 3번 b4","2 3번 b10","3 6번 b10","4 3번 자연혼재","5 6번 자연혼재",
    "A fixed","B tied","C bounded","D free","E c 작게","F c 크게",
    "G LQ c=0.5","H LQ c=0.75","I LQ c 학습","J b만 학습","K b만+중심화",
    "L tied 중심","M bounded 중심","N free 중심"];
  const gain = [-0.0281,-0.0076,-0.0114,-0.0035,-0.0035,
    -0.0014,-0.0333,-0.0271,-0.0310,-0.0333,-0.0005,
    0.0024,-0.0019,0.0019,-0.0176,-0.0148,-0.0181,-0.0243,-0.0129];

  s.addChart(pres.ChartType.bar, [{ name: "LS 보탠 양", labels, values: gain }], {
    x: M, y: 2.2, w: 8.5, h: 4.75, barDir: "bar", barGapWidthPct: 45,
    chartColors: [LS], ...chartFrame(),
    showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: "0.000;-0.000",
    valAxisMinVal: -0.04, valAxisMaxVal: 0.012, valAxisLabelFormatCode: "0.00",
    catAxisLabelFontSize: 9,
  });

  card(s, { x: 9.45, y: 2.2, w: 3.25, h: 2.1, fill: "FBF1EE" });
  s.addText("19개 중 2개", {
    x: 9.75, y: 2.42, w: 2.7, h: 0.5, isTextBox: true, margin: 0,
    fontFace: NUM, fontSize: 26, bold: true, color: LS,
  });
  s.addText("LS에서 자기 prior를 넘은 조건. 그마저 +0.002다.\n\n지금 모델에서 피해 데이터가 LS 순위에 보태는 것이 사실상 없다.", {
    x: 9.75, y: 2.94, w: 2.7, h: 1.2, isTextBox: true, margin: 0,
    fontFace: KR, fontSize: 12, color: INK2, lineSpacing: 17,
  });
  card(s, { x: 9.45, y: 4.5, w: 3.25, h: 2.45, fill: "EDF4F7" });
  s.addText("LQ는 반대다", {
    x: 9.75, y: 4.72, w: 2.7, h: 0.34, isTextBox: true, margin: 0,
    fontFace: KR, fontSize: 15, bold: true, color: LQ,
  });
  s.addText("LQ에서는 거의 모든 조건이 자기 prior를 넘는다(+0.004 ~ +0.024).\n\n예외는 3·5번(LQ 최대집계)으로, prior가 0.863인데 posterior가 0.804다.", {
    x: 9.75, y: 5.1, w: 2.7, h: 1.6, isTextBox: true, margin: 0,
    fontFace: KR, fontSize: 12, color: INK2, lineSpacing: 17,
  });
}

/* ══════════════════ 6. 핵심 1 — b를 학습하는가 ══════════════════ */
{
  const s = slideBase(false);
  head(s, "03", "한 축이 전부를 설명한다 — b를 학습하는가", false);
  s.addText("LS 예측 편향 = 평균 예측확률 − 실제 양성률. 0에 가까울수록 눈금이 맞다.", {
    x: M, y: 1.78, w: 11.6, h: 0.32, isTextBox: true, margin: 0,
    fontFace: KR, fontSize: 13, color: INK2,
  });

  const labels = ["A fixed","G LQ c=0.5","H LQ c=0.75","I LQ c 학습","F c 크게","E c 작게",
    "J b만 학습","K b만+중심화","C bounded","D free","L tied 중심","M bounded 중심",
    "N free 중심","B tied","2 3번 b10","3 6번 b10","1 3번 b4"];
  const fixedB = [0.006,0.008,0.007,0.008,0.146,-0.494, null,null,null,null,null,null,null,null,null,null,null];
  const learnB = [null,null,null,null,null,null, -0.270,-0.273,-0.235,-0.248,-0.268,-0.277,-0.201,-0.303,-0.210,-0.211,-0.308];

  s.addChart(pres.ChartType.bar, [
    { name: "b = 0 고정", labels, values: fixedB },
    { name: "b 학습", labels, values: learnB },
  ], {
    x: M, y: 2.2, w: 8.4, h: 4.75, barDir: "bar", barGrouping: "clustered", barGapWidthPct: 30,
    chartColors: [GOOD, LS], ...chartFrame(), showLegend: true, legendPos: "t",
    legendFontFace: KR, legendFontSize: 11, legendColor: INK2,
    showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: "+0.000;-0.000",
    valAxisMinVal: -0.55, valAxisMaxVal: 0.25, valAxisLabelFormatCode: "0.0",
  });

  card(s, { x: 9.35, y: 2.2, w: 3.35, h: 2.35, fill: "F1F5F7" });
  s.addText("왜 이런가", { x: 9.65, y: 2.42, w: 2.8, h: 0.34, isTextBox: true, margin: 0,
    fontFace: KR, fontSize: 15, bold: true, color: INK });
  s.addText("학습 목표는 피해 데이터의 marginal likelihood이지 GT가 아니다.\nGT는 학습에 전혀 들어가지 않는다.\n\n그래서 자유도를 주면 GT 눈금에서 멀어진다.", {
    x: 9.65, y: 2.8, w: 2.8, h: 1.6, isTextBox: true, margin: 0,
    fontFace: KR, fontSize: 12, color: INK2, lineSpacing: 17 });

  card(s, { x: 9.35, y: 4.75, w: 3.35, h: 2.2, fill: "FBF1EE" });
  s.addText("학습은 보정이 아니다", { x: 9.65, y: 4.97, w: 2.8, h: 0.34, isTextBox: true, margin: 0,
    fontFace: KR, fontSize: 15, bold: true, color: LS });
  s.addText("중심화하고 b 범위를 [−12, 12]로 넓혀 다시 돌려도(L·M·N) 나아지지 않았다.\n\nb 제약이 문제가 아니라 b를 학습하는 것 자체가 문제다.", {
    x: 9.65, y: 5.35, w: 2.8, h: 1.5, isTextBox: true, margin: 0,
    fontFace: KR, fontSize: 12, color: INK2, lineSpacing: 17 });
  s.addNotes("b=0 고정 중 E와 F가 큰 편향을 보이는 건 c를 잘못 준 탓이고, c_LS=1인 조건은 전부 +0.006~0.008.");
}

/* ══════════════════ 7. 핵심 2 — 면적 항을 버린다 ══════════════════ */
{
  const s = slideBase(false);
  head(s, "03", "자유도를 주면 면적 항 자체를 버린다", false);
  s.addText("c_LS는 면적 항의 세기다. 학습에 맡길수록 0으로 간다.", {
    x: M, y: 1.78, w: 11.6, h: 0.32, isTextBox: true, margin: 0,
    fontFace: KR, fontSize: 13, color: INK2,
  });

  const labels = ["A fixed\n(c 고정)", "B tied\n(c = a)", "C bounded\n(c=1 고정)", "D free", "N free 중심화"];
  s.addChart(pres.ChartType.bar, [{ name: "c_LS", labels, values: [1.0, 0.6801, 1.0, 0.3639, 0.0052] }], {
    x: M, y: 2.35, w: 5.9, h: 4.3, barDir: "col", barGapWidthPct: 55,
    chartColors: [LQ], ...chartFrame(),
    showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: "0.000",
    valAxisMinVal: 0, valAxisMaxVal: 1.15, valAxisLabelFormatCode: "0.0",
    catAxisLabelFontSize: 10,
  });
  s.addText("학습된 c_LS — 면적 항의 세기", {
    x: M, y: 6.7, w: 5.9, h: 0.3, isTextBox: true, margin: 0, align: "center",
    fontFace: KR, fontSize: 11, color: INK3 });

  s.addChart(pres.ChartType.bar, [{ name: "자기 prior LS AUC", labels, values: [0.8410, 0.8410, 0.8257, 0.7990, 0.7490] }], {
    x: 6.85, y: 2.35, w: 5.85, h: 4.3, barDir: "col", barGapWidthPct: 55,
    chartColors: [LS], ...chartFrame(),
    showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: "0.000",
    valAxisMinVal: 0.70, valAxisMaxVal: 0.88, valAxisLabelFormatCode: "0.00",
    catAxisLabelFontSize: 10,
  });
  s.addText("그 결과 — prior 순위가 USGS 원값(0.7486) 수준으로 돌아간다", {
    x: 6.85, y: 6.7, w: 5.85, h: 0.3, isTextBox: true, margin: 0, align: "center",
    fontFace: KR, fontSize: 11, color: INK3 });
  s.addNotes("순위를 올려 주던 바로 그 항을 피해 likelihood가 버린다. free-ctr은 c_LS=0.005.");
}

/* ══════════════════ 8. ② b 범위 ══════════════════ */
{
  const s = slideBase(false);
  head(s, "04", "② b 범위 — 넓혀도 상한에 붙는다", false);
  s.addText("제약된 b가 상한에 붙어 나오면 최적값을 찾은 것인지 잘라낸 것인지 알 수 없다.\n그래서 다른 조건을 그대로 두고 상한만 넓혀 안쪽에서 멈추는지 봤다.", {
    x: M, y: 1.78, w: 11.6, h: 0.6, isTextBox: true, margin: 0,
    fontFace: KR, fontSize: 13, color: INK2, lineSpacing: 19,
  });

  [["상한 4", 4, 3.9541, 98.9], ["상한 10", 10, 9.5230, 95.2]].forEach(([lab, bound, got, pct], i) => {
    const y = 2.72 + i * 1.12;
    const trackW = 8.3, scale = trackW / 10;
    s.addText(lab, { x: M, y: y + 0.08, w: 1.1, h: 0.34, isTextBox: true, margin: 0,
      fontFace: KR, fontSize: 14, bold: true, color: INK2 });
    s.addShape(pres.ShapeType.roundRect, { x: M + 1.2, y, w: bound * scale, h: 0.5,
      rectRadius: 0.04, fill: { color: BG2 }, line: { color: "D5DDE2", width: 1 } });
    s.addShape(pres.ShapeType.roundRect, { x: M + 1.2, y, w: got * scale, h: 0.5,
      rectRadius: 0.04, fill: { color: LS } });
    s.addText(`${got.toFixed(2)} / ${bound}`, {
      x: M + 1.36 + bound * scale, y: y + 0.08, w: 1.9, h: 0.34, isTextBox: true, margin: 0,
      fontFace: NUM, fontSize: 14, bold: true, color: INK });
    s.addText(`상한의 ${pct}%`, { x: M + 1.3, y: y + 0.54, w: 2.4, h: 0.28, isTextBox: true, margin: 0,
      fontFace: KR, fontSize: 11, color: INK3 });
  });

  card(s, { x: M, y: 5.12, w: 5.9, h: 1.72, fill: "FBF1EE" });
  s.addText("b는 안쪽 최적점이 없다", { x: M + 0.32, y: 5.32, w: 5.3, h: 0.34, isTextBox: true, margin: 0,
    fontFace: KR, fontSize: 15, bold: true, color: LS });
  s.addText("likelihood가 계속 b를 키우려 하고 상한이 그걸 자르고 있을 뿐이다.\n면적 조건에서도 bounded의 b_LQ가 −1.947로 하한 −2에 붙었다.", {
    x: M + 0.32, y: 5.7, w: 5.3, h: 1.0, isTextBox: true, margin: 0,
    fontFace: KR, fontSize: 12, color: INK2, lineSpacing: 17 });

  card(s, { x: 6.8, y: 5.12, w: 5.9, h: 1.72, fill: "EDF4F7" });
  s.addText("LQ 최대집계(6번)가 드러낸 것", { x: 7.12, y: 5.32, w: 5.3, h: 0.34, isTextBox: true, margin: 0,
    fontFace: KR, fontSize: 15, bold: true, color: LQ });
  s.addText("LQ prior를 최대집계로 바꾸자 prior 자체의 AUC가 0.749 → 0.863으로 올랐다.\n그런데 posterior는 0.804 — 자기 prior보다 0.06 낮다.", {
    x: 7.12, y: 5.7, w: 5.3, h: 1.0, isTextBox: true, margin: 0,
    fontFace: KR, fontSize: 12, color: INK2, lineSpacing: 17 });
}

/* ══════════════════ 9. ③ 자연+혼재 ══════════════════ */
{
  const s = slideBase(false);
  head(s, "05", "③ 자연+혼재 — 모델이 아니라 정답을 고쳤다", false);
  s.addText("USGS 산사태 사전모형이 설명하는 것은 자연사면의 붕괴다. 그런데 GT의 양성에는\n성토·옹벽·법면 같은 인공사면 붕괴가 섞여 있었다.", {
    x: M, y: 1.78, w: 11.6, h: 0.6, isTextBox: true, margin: 0,
    fontFace: KR, fontSize: 13, color: INK2, lineSpacing: 19,
  });

  const rules = [["자연 / 혼재", "양성 유지", "77"], ["인공", "음성(0) — 평가에는 남긴다", "8"],
                 ["불명", "평가에서 제외", "20"], ["ls_flag = 0", "음성 유지", "20"]];
  s.addTable([
    [{ text: "ls_type", options: { bold: true } }, { text: "처리", options: { bold: true } },
     { text: "행", options: { bold: true, align: "right" } }],
    ...rules.map(r => [r[0], r[1], { text: r[2], options: { align: "right", fontFace: NUM } }]),
  ], {
    x: M, y: 2.6, w: 6.0, colW: [1.6, 3.6, 0.8], rowH: 0.42,
    fontFace: KR, fontSize: 12, color: INK2, border: { type: "solid", color: "E3E9EC", pt: 1 },
    fill: { color: BG }, valign: "middle",
  });

  s.addChart(pres.ChartType.bar, [
    { name: "USGS prior 단독", labels: ["기존 GT", "자연+혼재 GT"], values: [0.7486, 0.8179] },
    { name: "posterior", labels: ["기존 GT", "자연+혼재 GT"], values: [0.7410, 0.8145] },
  ], {
    x: 7.15, y: 2.5, w: 5.55, h: 3.1, barDir: "col", barGrouping: "clustered", barGapWidthPct: 45,
    chartColors: [PRIOR, LS], ...chartFrame(), showLegend: true, legendPos: "t",
    legendFontFace: KR, legendFontSize: 11, legendColor: INK2,
    showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: "0.000",
    valAxisMinVal: 0.70, valAxisMaxVal: 0.86, valAxisLabelFormatCode: "0.00",
    catAxisLabelFontSize: 11,
  });

  card(s, { x: M, y: 4.86, w: 6.0, h: 1.98, fill: "FBF1EE" });
  s.addText("모델을 한 줄도 바꾸지 않았다", { x: M + 0.32, y: 5.06, w: 5.4, h: 0.34, isTextBox: true, margin: 0,
    fontFace: KR, fontSize: 15, bold: true, color: LS });
  s.addText("그런데 USGS prior의 LS AUC가 0.7486 → 0.8179로 올랐다.\n원래 맞히고 있던 것을 그동안 틀렸다고 채점하고 있었다는 뜻이다.\n\n2번과 4번의 a_LS·b_LS·gamma_ls_max가 완전히 동일한 것으로 학습 불변을 확인했다.", {
    x: M + 0.32, y: 5.44, w: 5.4, h: 1.3, isTextBox: true, margin: 0,
    fontFace: KR, fontSize: 12, color: INK2, lineSpacing: 17 });

  s.addText("MSE 0.2510 → 0.1858 · 편향 −0.210 → −0.077", {
    x: 7.15, y: 5.75, w: 5.55, h: 0.34, isTextBox: true, margin: 0, align: "center",
    fontFace: KR, fontSize: 13, bold: true, color: INK2 });
  s.addText("불명을 제외한 이유 — 자료에 사면 종별 기술이 없다는 뜻이지 인공이라는 근거가 아니다.", {
    x: 7.15, y: 6.14, w: 5.55, h: 0.5, isTextBox: true, margin: 0, align: "center",
    fontFace: KR, fontSize: 11, color: INK3, lineSpacing: 15 });
}

/* ══════════════════ 10. ④ c를 hazard별로 ══════════════════ */
{
  const s = slideBase(false);
  head(s, "06", "④ 면적 항 — c를 hazard별로 나눠야 한다", false);
  s.addText("c = 1은 “칸끼리 독립”에서 나온 값이다. 기존 조건은 이 c를 두 hazard에 똑같이 강요했다.", {
    x: M, y: 1.78, w: 11.6, h: 0.32, isTextBox: true, margin: 0,
    fontFace: KR, fontSize: 13, color: INK2,
  });
  hazardChip(s, M, 2.28, "LS");
  hazardChip(s, M + 2.1, 2.28, "LQ");

  s.addChart(pres.ChartType.bar, [
    { name: "LS 편향", labels: ["c = 0.5", "c = 1.0", "c = 2.0"], values: [-0.494, 0.006, 0.146] },
    { name: "LQ 편향", labels: ["c = 0.5", "c = 1.0", "c = 2.0"], values: [-0.103, 0.256, 0.501] },
  ], {
    x: M, y: 2.7, w: 6.4, h: 4.0, barDir: "col", barGrouping: "clustered", barGapWidthPct: 45,
    chartColors: [LS, LQ], ...chartFrame(), showLegend: true, legendPos: "t",
    legendFontFace: KR, legendFontSize: 11, legendColor: INK2,
    showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: "+0.000;-0.000",
    valAxisMinVal: -0.6, valAxisMaxVal: 0.62, valAxisLabelFormatCode: "0.0",
    catAxisLabelFontSize: 11,
  });
  s.addText("예측 편향 — 0에 가까울수록 눈금이 맞다", {
    x: M, y: 6.72, w: 6.4, h: 0.3, isTextBox: true, margin: 0, align: "center",
    fontFace: KR, fontSize: 11, color: INK3 });

  card(s, { x: 7.35, y: 2.7, w: 5.35, h: 1.85, fill: "FBF1EE" });
  s.addText("LS는 유도식에서 이미 맞는다", { x: 7.65, y: 2.9, w: 4.8, h: 0.34, isTextBox: true, margin: 0,
    fontFace: KR, fontSize: 15, bold: true, color: LS });
  s.addText("c = 1에서 편향 +0.006. 건드릴 이유가 없다.\n반면 LQ는 같은 값에서 +0.256 과대예측이고, 최적값은 0.5~1 사이다.", {
    x: 7.65, y: 3.28, w: 4.8, h: 1.2, isTextBox: true, margin: 0,
    fontFace: KR, fontSize: 12, color: INK2, lineSpacing: 17 });

  card(s, { x: 7.35, y: 4.75, w: 5.35, h: 1.95, fill: "EDF4F7" });
  s.addText("물리적으로도 말이 된다", { x: 7.65, y: 4.95, w: 4.8, h: 0.34, isTextBox: true, margin: 0,
    fontFace: KR, fontSize: 15, bold: true, color: LQ });
  s.addText("액상화 감수성은 충적층·지질을 따라 공간적으로 강하게 상관된다.\n그러면 1 − ∏(1−pᵢ)가 과대추정한다 — 유효 칸 수가 명목 k보다 작다는 뜻이고, 그것이 c_LQ < 1로 나타난다.", {
    x: 7.65, y: 5.33, w: 4.8, h: 1.3, isTextBox: true, margin: 0,
    fontFace: KR, fontSize: 12, color: INK2, lineSpacing: 17 });
}

/* ══════════════════ 11. ④ 답 ══════════════════ */
{
  const s = slideBase(false);
  head(s, "06", "답 — c_LS는 유도식, c_LQ만 낮춘다", false);

  const hdr = ["#", "조건", "학습", "c_LS", "c_LQ", "LS AUC", "LS 보탠양", "LS MSE", "LQ AUC", "LQ 보탠양", "LQ MSE"];
  const rows = [
    ["A", "fixed", "0", "1.00", "1.00", "0.8395", "−0.001", "0.0998", "0.8226", "+0.004", "0.2497"],
    ["G", "LQ c=0.5", "0", "1.00", "0.50", "0.8433", "+0.002", "0.0994", "0.8171", "+0.019", "0.1929"],
    ["H", "LQ c=0.75", "0", "1.00", "0.75", "0.8390", "−0.002", "0.0998", "0.8240", "+0.011", "0.1868"],
    ["I", "LQ c 학습", "1", "1.00", "0.43", "0.8429", "+0.002", "0.0993", "0.8145", "+0.024", "0.2155"],
    ["C", "bounded", "4", "1.00", "1.00", "0.7986", "−0.027", "0.2269", "0.8297", "+0.014", "0.1722"],
    ["J", "b만 학습", "2", "1.00", "1.00", "0.8233", "−0.018", "0.2202", "0.8350", "+0.017", "0.2219"],
  ];
  const hi = new Set(["G", "H", "I"]);
  s.addTable([
    hdr.map((h, i) => ({ text: h, options: { bold: true, color: INK, fill: { color: BG2 },
      align: i >= 2 ? "right" : "left", fontSize: 11 } })),
    ...rows.map(r => r.map((c, i) => ({
      text: c,
      options: {
        align: i >= 2 ? "right" : "left",
        fontFace: i >= 2 ? NUM : KR,
        bold: hi.has(r[0]),
        color: hi.has(r[0]) ? INK : INK2,
        fill: { color: hi.has(r[0]) ? "EAF4EE" : BG },
      },
    }))),
  ], {
    x: M, y: 2.05, w: 12.1, colW: [0.5, 1.6, 0.7, 0.8, 0.8, 1.2, 1.3, 1.2, 1.2, 1.3, 1.5],
    rowH: 0.42, fontFace: KR, fontSize: 11.5, valign: "middle",
    border: { type: "solid", color: "E3E9EC", pt: 1 },
  });

  s.addText("‘보탠 양’ = posterior AUC − 자기 prior AUC.  기저확률 MSE 베이스라인 LS 0.1344 / LQ 0.2494.  전체 14개 조건은 부록 CSV에.", {
    x: M, y: 5.05, w: 12.1, h: 0.3, isTextBox: true, margin: 0,
    fontFace: KR, fontSize: 11, color: INK3 });

  card(s, { x: M, y: 5.5, w: 12.1, h: 1.35, fill: "EAF4EE" });
  s.addText("답은 G 아니면 H다", { x: M + 0.34, y: 5.68, w: 5.0, h: 0.34, isTextBox: true, margin: 0,
    fontFace: KR, fontSize: 16, bold: true, color: GOOD });
  s.addText("네 지표를 모두 통과하는 것은 G와 I. H는 LS AUC가 자기 prior보다 0.002 낮아 형식상 3/4이지만 LQ MSE는 14개 중 가장 좋다(0.1868).\n공통점이 본질이다 — 셋 다 c_LS=1(유도식)을 지키고 c_LQ < 1로 낮췄으며 학습 파라미터가 0~1개다. I가 학습한 c_LQ=0.434는 G의 고정값 0.5보다 LQ MSE가 나쁘다.", {
    x: M + 0.34, y: 6.06, w: 11.4, h: 0.7, isTextBox: true, margin: 0,
    fontFace: KR, fontSize: 12, color: INK2, lineSpacing: 17 });
}

/* ══════════════════ 12. 중심화 ══════════════════ */
{
  const s = slideBase(false);
  head(s, "07", "log k 중심화 — 빼도 되고 안 빼도 된다", false);
  s.addText("z = a·log p̄ + b + c·(log k − m)  =  a·log p̄ + (b − c·m) + c·log k", {
    x: M, y: 1.82, w: 11.6, h: 0.4, isTextBox: true, margin: 0,
    fontFace: NUM, fontSize: 17, bold: true, color: INK,
  });
  s.addText("b가 흡수하는 순수 재매개변수화다. 같은 조건을 중심화만 달리해 돌려 확인했다.", {
    x: M, y: 2.28, w: 11.6, h: 0.32, isTextBox: true, margin: 0,
    fontFace: KR, fontSize: 13, color: INK2,
  });

  s.addTable([
    [{ text: "조건", options: { bold: true } }, { text: "b_LS", options: { bold: true, align: "right" } },
     { text: "b_LQ", options: { bold: true, align: "right" } }, { text: "중심 m", options: { bold: true, align: "right" } },
     { text: "LS AUC", options: { bold: true, align: "right" } }, { text: "LQ AUC", options: { bold: true, align: "right" } }],
    ["J  비중심화", "−2.488", "−3.967", "—", "0.8233", "0.8350"].map((c, i) => ({
      text: c, options: { align: i ? "right" : "left", fontFace: i ? NUM : KR } })),
    ["K  중심화", "+5.531", "+2.689", "8.042 / 6.656", "0.8262", "0.8349"].map((c, i) => ({
      text: c, options: { align: i ? "right" : "left", fontFace: i ? NUM : KR } })),
  ], {
    x: M, y: 2.78, w: 8.2, colW: [1.7, 1.2, 1.2, 1.9, 1.1, 1.1], rowH: 0.46,
    fontFace: KR, fontSize: 12, color: INK2, valign: "middle",
    border: { type: "solid", color: "E3E9EC", pt: 1 }, fill: { color: BG },
  });
  s.addText("K의 b − m = 5.531 − 8.042 = −2.511 ≈ J의 −2.488.   LQ는 2.689 − 6.656 = −3.967로 소수점까지 일치한다.", {
    x: M, y: 4.28, w: 8.2, h: 0.32, isTextBox: true, margin: 0,
    fontFace: KR, fontSize: 12, color: INK3 });

  card(s, { x: M, y: 4.8, w: 8.2, h: 2.05, fill: "EAF4EE" });
  s.addText("규칙 — 코드에 강제했다", { x: M + 0.34, y: 4.98, w: 7.5, h: 0.34, isTextBox: true, margin: 0,
    fontFace: KR, fontSize: 15, bold: true, color: GOOD });
  bullets(s, M + 0.34, 5.36, 7.5, 1.4, [
    "b를 학습하면 중심화한다 — 결과는 같지만 b가 “평균 크기 시정촌에서의 log-odds”라는 뜻을 갖고 b·c 상관이 줄어 최적화가 안정적이다.",
    "b = 0 고정이면 중심화하지 않는다 — 재매개변수화가 아니라 다른 모형이 된다. 안 뺀 z = log(p̄·k) = log λ 가 유도식 그 자체다.",
    "어느 쪽이든 AUC는 변하지 않는다. 바뀌는 것은 MSE(눈금)뿐이다.",
  ], 12);

  card(s, { x: 9.1, y: 2.78, w: 3.6, h: 4.07, fill: "FBF1EE" });
  s.addText("그래서 얻은 것", { x: 9.42, y: 3.0, w: 3.05, h: 0.34, isTextBox: true, margin: 0,
    fontFace: KR, fontSize: 15, bold: true, color: LS });
  s.addText("중심화 + b 범위 [−12, 12]로 다시 돌린 L·M·N도 기존 B·C·D보다 나아지지 않았다.\n\nb가 하한에 붙어 있던 것이 문제가 아니었다는 뜻이다.\n\nb를 학습하는 것 자체가 LS 눈금을 무너뜨린다.", {
    x: 9.42, y: 3.4, w: 3.05, h: 3.2, isTextBox: true, margin: 0,
    fontFace: KR, fontSize: 12, color: INK2, lineSpacing: 17 });
}

/* ══════════════════ 13. 면적 편향 경고 ══════════════════ */
{
  const s = slideBase(false);
  head(s, "08", "경고 — 면적만으로도 LS AUC 0.78이 나온다", false);
  s.addText("각 점수만으로 순위를 매겼을 때의 AUC. A(fixed, lam 10) 조건에서 계산했다.", {
    x: M, y: 1.78, w: 11.6, h: 0.32, isTextBox: true, margin: 0,
    fontFace: KR, fontSize: 13, color: INK2,
  });

  const labels = ["USGS prior 그대로", "면적만 (log k)", "prior + 면적", "최종 posterior"];
  s.addChart(pres.ChartType.bar, [
    { name: "LS", labels, values: [0.7486, 0.7833, 0.8410, 0.8395] },
    { name: "LQ", labels, values: [0.7485, 0.5852, 0.8183, 0.8226] },
  ], {
    x: M, y: 2.3, w: 7.4, h: 4.3, barDir: "bar", barGrouping: "clustered", barGapWidthPct: 40,
    chartColors: [LS, LQ], ...chartFrame(), showLegend: true, legendPos: "t",
    legendFontFace: KR, legendFontSize: 11, legendColor: INK2,
    showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: "0.000",
    valAxisMinVal: 0.5, valAxisMaxVal: 0.92, valAxisLabelFormatCode: "0.0",
    catAxisLabelFontSize: 10,
  });

  card(s, { x: 8.35, y: 2.3, w: 4.35, h: 2.2, fill: "FBF1EE" });
  s.addText("노출·탐지 편향", { x: 8.67, y: 2.5, w: 3.8, h: 0.34, isTextBox: true, margin: 0,
    fontFace: KR, fontSize: 15, bold: true, color: LS });
  s.addText("LS에서 면적만으로도 USGS prior 단독보다 높다. 넓은 시정촌일수록 산사태가 기록될 확률이 높다는 뜻이다.\n자연+혼재 GT에서는 0.655로 떨어진다 — 편향의 상당 부분이 인공사면·불명 행에서 왔다.", {
    x: 8.67, y: 2.88, w: 3.8, h: 1.5, isTextBox: true, margin: 0,
    fontFace: KR, fontSize: 12, color: INK2, lineSpacing: 17 });

  card(s, { x: 8.35, y: 4.7, w: 4.35, h: 1.9, fill: "EDF4F7" });
  s.addText("LQ는 이 문제가 없다", { x: 8.67, y: 4.9, w: 3.8, h: 0.34, isTextBox: true, margin: 0,
    fontFace: KR, fontSize: 15, bold: true, color: LQ });
  s.addText("면적만의 AUC가 0.585로 거의 무작위다.\nLQ 쪽 면적 항 개선은 편향으로 설명되지 않는다 — 진짜 효과다.", {
    x: 8.67, y: 5.28, w: 3.8, h: 1.2, isTextBox: true, margin: 0,
    fontFace: KR, fontSize: 12, color: INK2, lineSpacing: 17 });
}

/* ══════════════════ 14. 한계와 다음 ══════════════════ */
{
  const s = slideBase(true);
  head(s, "09", "한계와 다음", true);

  const items = [
    ["가장 큰 미해결 — 피해 likelihood가 LS 순위를 깎는다",
     "19개 중 LS에서 자기 prior를 넘은 것은 둘뿐이고 그마저 +0.002다. 왜 그런지가 다음 연구의 중심이어야 한다.", LS],
    ["③과 ④를 아직 결합하지 않았다",
     "면적 항 14개 조건은 전부 기존(all) GT로 돌았다. 자연+혼재 GT에서 다시 재면 두 개선이 겹치는지 알 수 있다.", WARN],
    ["면적 편향을 가르지 못했다",
     "면적을 offset으로 고정하고 남는 효과만 보는 설계가 필요하다.", WARN],
    ["LQ 최대집계 + 면적 항을 안 해봤다",
     "가장 좋은 LQ prior(0.8634)와 면적 항을 한 번도 같이 쓰지 않았다. 다만 λ = p̄·k 유도는 평균집계를 전제하므로 이론 정리가 먼저다.", LQ],
    ["평가 행이 적고 쏠려 있다",
     "LS 125행 중 양성 105행(84%), 9개 이벤트 중 4개는 AUC가 정의되지 않는다. 2004 니가타는 10행뿐이다.", INK3],
  ];
  items.forEach(([t, d, c], i) => {
    const y = 1.92 + i * 1.02;
    s.addShape(pres.ShapeType.ellipse, { x: M, y: y + 0.08, w: 0.22, h: 0.22, fill: { color: c } });
    s.addText(t, { x: M + 0.44, y: y, w: 11.6, h: 0.34, isTextBox: true, margin: 0,
      fontFace: KR, fontSize: 15, bold: true, color: BG });
    s.addText(d, { x: M + 0.44, y: y + 0.36, w: 11.6, h: 0.5, isTextBox: true, margin: 0,
      fontFace: KR, fontSize: 12, color: "AFC0CB", lineSpacing: 16 });
  });
  s.addText("재현:  python tools/build_dataset.py --area-from-usgs  →  python run_followup3.py --data-dir .", {
    x: M, y: 7.0, w: 11.6, h: 0.3, isTextBox: true, margin: 0,
    fontFace: NUM, fontSize: 11, color: INK3 });
}

pres.writeFile({ fileName: "후속실험3.pptx" }).then(f => console.log("생성:", f));
