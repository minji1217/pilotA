const pptxgen = require("pptxgenjs");
const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE";            // 13.3 x 7.5
pres.author = "Pilot A";
pres.title = "파일럿A 후속실험 3 — LOEO + 산지 정답 학습";

const DARK="2E2422", TERRA="B85042", SAGE="5F7F6E", SAND="F2EFE6",
      INK="2E2422", MUTED="7A6A63", WHITE="FFFFFF", LINE="DCD6CC", GOLD="C98B3A";
const H="Cambria", B="Calibri";
const W=13.333, HT=7.5;

const title=(s,t,sub)=>{
  s.addText(t,{x:0.7,y:0.42,w:11.9,h:0.62,fontSize:34,bold:true,color:INK,fontFace:H,isTextBox:true,margin:0});
  if(sub) s.addText(sub,{x:0.7,y:1.06,w:11.9,h:0.38,fontSize:14,color:MUTED,fontFace:B,isTextBox:true,margin:0});
};
const card=(s,x,y,w,h,fill)=>s.addShape(pres.ShapeType.roundRect,{x,y,w,h,rectRadius:0.09,
  fill:{color:fill||SAND},line:{color:LINE,width:0.5}});
const num=(s,x,y,n,c)=>{
  s.addShape(pres.ShapeType.ellipse,{x,y,w:0.42,h:0.42,fill:{color:c||TERRA},line:{color:c||TERRA,width:0}});
  s.addText(String(n),{x,y,w:0.42,h:0.42,fontSize:15,bold:true,color:WHITE,align:"center",valign:"middle",fontFace:H,isTextBox:true,margin:0});
};
const tbl=(s,rows,opt)=>s.addTable(rows,Object.assign({
  border:{type:"solid",color:LINE,pt:0.5},fontFace:B,fontSize:11,color:INK,valign:"middle",
  autoPage:false},opt));
const hdr=t=>({text:t,options:{bold:true,color:WHITE,fill:{color:DARK},fontSize:10.5,align:"center"}});
const chartFrame={showTitle:false,showLegend:false,catAxisLabelColor:MUTED,valAxisLabelColor:MUTED,
  catAxisLabelFontSize:11,valAxisLabelFontSize:10,catAxisLabelFontFace:B,valAxisLabelFontFace:B,
  valGridLine:{color:"EDE8E0",size:1},catGridLine:{style:"none"},
  showValue:true,dataLabelFontSize:11,dataLabelFontFace:B,dataLabelColor:INK,dataLabelPosition:"outEnd",
  dataLabelFormatCode:"0.000"};

/* ───────────────────────── 1. 표지 ───────────────────────── */
let s=pres.addSlide(); s.background={color:DARK};
s.addText("파일럿A · 후속실험 3",{x:0.85,y:1.5,w:8,h:0.34,fontSize:13,color:TERRA,bold:true,charSpacing:2,fontFace:B,isTextBox:true,margin:0});
s.addText("지진 하나씩 가리기(LOEO)와\n산지 정답 학습",{x:0.85,y:2.0,w:8.3,h:1.75,fontSize:40,bold:true,color:WHITE,lineSpacing:46,fontFace:H,isTextBox:true,margin:0});
s.addText("면적 항 prior 위에서 산사태 정답을 학습에 쓰면 정말 좋아지는가",
  {x:0.85,y:3.92,w:8.3,h:0.4,fontSize:15,color:"CFC4BC",fontFace:B,isTextBox:true,margin:0});
s.addShape(pres.ShapeType.line,{x:0.85,y:4.62,w:3.0,h:0,line:{color:TERRA,width:2.5}});
s.addText("학습 30회 · LOEO 5회차 · 부트스트랩 3,000회 (seed 0)\n사전등록 조건 §3–§4를 결과 확인 전에 고정",
  {x:0.85,y:4.85,w:8.3,h:0.8,fontSize:12.5,color:"A99A92",lineSpacing:20,fontFace:B,isTextBox:true,margin:0});
[["0.8550","최고 LS 가중 AUC"],["0개","그 조건의 prior 학습 파라미터"],["5회차","지진별 교차검증"]]
 .forEach(([v,l],i)=>{
  const y=1.62+i*1.55;
  s.addShape(pres.ShapeType.roundRect,{x:9.65,y,w:3.0,h:1.3,rectRadius:0.09,fill:{color:"3B2E2A"},line:{color:"52403A",width:0.75}});
  s.addText(v,{x:9.85,y:y+0.17,w:2.6,h:0.62,fontSize:30,bold:true,color:i===0?TERRA:WHITE,fontFace:H,isTextBox:true,margin:0});
  s.addText(l,{x:9.85,y:y+0.80,w:2.6,h:0.36,fontSize:10.5,color:"A99A92",fontFace:B,isTextBox:true,margin:0});
});
s.addNotes("후속실험 3의 목적은 교수님 제안(산사태 정답을 학습에 쓰되 지진을 하나씩 가려 공정하게 평가)을 기존 prior와 면적 항 prior 두 가지 위에서 검증하는 것이다.");

/* ───────────────────────── 2. 한 장 요약 ───────────────────────── */
s=pres.addSlide(); s.background={color:WHITE};
title(s,"한 장 요약","30회 실행 결과를 세 문장으로");
[["제안은 A 계열에서 깨끗하게 작동했다",
  "LS 가중 AUC 0.7222 → 0.8039. 짝지은 부트스트랩에서 P(개선>0)=0.981이고, 5회차 κ가 전부 양수(+0.93~+1.37)로 안정적이었다."],
 ["그러나 면적 항 위에서는 이득이 없다",
  "B2 0.8507 ≤ B0 0.8550. 면적 항이 산지 비율의 정보를 이미 담고 있어(corr 0.53) 추가로 배울 것이 없었다. κ 부호도 회차마다 뒤집혔다."],
 ["가장 좋은 구성은 가장 적게 학습하는 것",
  "B0 — prior 학습 파라미터 0개, 산사태 정답 미사용. LS 0.8550 / LQ 0.7812로 모든 조건 중 1위다."]]
 .forEach(([t,d],i)=>{
  const y=1.66+i*1.42;
  card(s,0.7,y,8.5,1.24);
  num(s,0.95,y+0.2,i+1);
  s.addText(t,{x:1.5,y:y+0.14,w:7.5,h:0.36,fontSize:15.5,bold:true,color:INK,fontFace:H,isTextBox:true,margin:0});
  s.addText(d,{x:1.5,y:y+0.53,w:7.5,h:0.62,fontSize:11.5,color:MUTED,lineSpacing:15,fontFace:B,isTextBox:true,margin:0});
});
s.addShape(pres.ShapeType.roundRect,{x:9.5,y:1.66,w:3.15,h:4.18,rectRadius:0.09,fill:{color:DARK},line:{color:DARK,width:0}});
s.addText("추가로 확인한 것",{x:9.75,y:1.9,w:2.7,h:0.32,fontSize:12,bold:true,color:TERRA,fontFace:B,isTextBox:true,margin:0});
s.addText("사전등록 밖 사후 탐색으로 b_LQ 고정을 풀었더니",
  {x:9.75,y:2.3,w:2.7,h:0.6,fontSize:11,color:"CFC4BC",lineSpacing:15,fontFace:B,isTextBox:true,margin:0});
s.addText("LQ 0.7812",{x:9.75,y:2.95,w:2.7,h:0.4,fontSize:16,color:"8E7F78",strike:true,fontFace:H,isTextBox:true,margin:0});
s.addText("→ 0.8158",{x:9.75,y:3.35,w:2.7,h:0.55,fontSize:26,bold:true,color:WHITE,fontFace:H,isTextBox:true,margin:0});
s.addText("P(개선>0) = 0.978\n순위 식은 한 자리도 바뀌지 않았고 확률 수준만 고쳐졌다.",
  {x:9.75,y:4.0,w:2.7,h:1.0,fontSize:10.5,color:"A99A92",lineSpacing:14,fontFace:B,isTextBox:true,margin:0});
s.addText("기준값: USGS prior 단독 0.797 · 산지 비율 단독 0.806 · 면적 항 prior 단독 0.840 · 면적 항 사후(기존 자료) 0.855",
  {x:0.7,y:6.28,w:11.95,h:0.34,fontSize:10.5,color:MUTED,italic:true,fontFace:B,isTextBox:true,margin:0});
s.addNotes("핵심은 제안이 방법으로서는 작동했지만, 면적 항이라는 구조적 수정이 이미 같은 정보를 담고 있어 추가 이득이 없었다는 것이다.");

/* ───────────────────────── 3. 배경 ───────────────────────── */
s=pres.addSlide(); s.background={color:WHITE};
title(s,"왜 이 실험을 했는가","지금 모델은 피해 건수(NLL)만 보고 학습하고, 산사태 정답(ls_flag)은 평가에만 쓴다");
[["산지 비율은 그 자체로 잘 맞힌다","단독 LS 가중 AUC 0.806",SAGE],
 ["그런데 회귀식에 넣으면 떨어진다","LS AUC 0.651로 하락",TERRA],
 ["prior에 κ·m으로 넣어도 안 배운다","κ = 0.05, 사실상 0",TERRA]]
 .forEach(([t,d,c],i)=>{
  const x=0.7+i*4.0;
  card(s,x,1.72,3.7,1.55);
  s.addShape(pres.ShapeType.ellipse,{x:x+0.28,y:1.98,w:0.3,h:0.3,fill:{color:c},line:{color:c,width:0}});
  s.addText(t,{x:x+0.28,y:2.42,w:3.15,h:0.55,fontSize:12.5,bold:true,color:INK,lineSpacing:16,fontFace:H,isTextBox:true,margin:0});
  s.addText(d,{x:x+0.28,y:2.95,w:3.15,h:0.3,fontSize:11,color:MUTED,fontFace:B,isTextBox:true,margin:0});
});
s.addShape(pres.ShapeType.roundRect,{x:0.7,y:3.6,w:11.95,h:1.15,rectRadius:0.09,fill:{color:DARK},line:{color:DARK,width:0}});
s.addText("교수님 제안",{x:1.0,y:3.8,w:2.2,h:0.32,fontSize:12,bold:true,color:TERRA,fontFace:B,isTextBox:true,margin:0});
s.addText("산사태 정답을 학습에도 쓰되, 공정하게 평가하려고 지진을 하나씩 가려서 시험한다.",
  {x:1.0,y:4.14,w:11.3,h:0.42,fontSize:15,color:WHITE,fontFace:H,isTextBox:true,margin:0});
s.addText("이 제안을 두 가지 prior 위에서 실행했다",{x:0.7,y:5.0,w:11.95,h:0.34,fontSize:12.5,bold:true,color:INK,fontFace:B,isTextBox:true,margin:0});
tbl(s,[
 [hdr("계열"),hdr("LS prior 점수 z_LS"),hdr("LQ prior 점수 z_LQ"),hdr("학습 파라미터")],
 ["A (기존)","a·logit(π_LS) + b_LS  ( + κ·m )","a·logit(π_LQ) + b_LQ","a, b, κ"],
 ["B (면적 항)","log(π_LS) + log k_LS + b_LS  ( + κ·m )","log(π_LQ) + log k_LQ  (고정)","b_LS, κ"]],
 {x:0.7,y:5.42,w:11.95,colW:[1.6,4.6,3.75,2.0],rowH:0.36,fontSize:11});
s.addText("k = 시정촌 총면적 ÷ 격자 한 칸 넓이  ·  LS는 7.5″ 칸, LQ는 15″ 칸  ·  m = 표준화한 산지 비율",
  {x:0.7,y:6.68,w:11.95,h:0.32,fontSize:10.5,color:MUTED,italic:true,fontFace:B,isTextBox:true,margin:0});
s.addNotes("A는 기존 prior, B는 면적 항 prior다. 면적 항은 USGS 값이 확률이 아니라 칸당 피복 비율이라는 점을 보정한다.");

/* ───────────────────────── 4. LOEO 설계 ───────────────────────── */
s=pres.addSlide(); s.background={color:WHITE};
title(s,"지진 하나씩 가리기(LOEO) 설계","정답을 학습에 쓰면서도 성능을 정직하게 재는 방법");
const steps=[["시험 지진 1개 선택","5개 지진을 돌아가며 한 번씩"],
             ["그 지진의 ls_flag만 가림","피해 건수는 NLL에 그대로 들어간다"],
             ["나머지 지진으로 BCE 학습","loss = 기존 loss + ω × Σ BCE"],
             ["가린 지진으로만 채점","정답을 안 본 예측으로 AUC를 낸다"]];
steps.forEach(([t,d],i)=>{
  const x=0.7+i*3.05;
  card(s,x,1.74,2.8,1.82);
  num(s,x+0.26,1.96,i+1);
  s.addText(t,{x:x+0.26,y:2.48,w:2.3,h:0.5,fontSize:12.5,bold:true,color:INK,lineSpacing:16,fontFace:H,isTextBox:true,margin:0});
  s.addText(d,{x:x+0.26,y:2.96,w:2.32,h:0.54,fontSize:10.5,color:MUTED,lineSpacing:13,fontFace:B,isTextBox:true,margin:0});
  if(i<3) s.addText("›",{x:x+2.78,y:2.42,w:0.3,h:0.4,fontSize:24,bold:true,color:TERRA,align:"center",fontFace:H,isTextBox:true,margin:0});
});
s.addText("5회차 구성",{x:0.7,y:3.68,w:6,h:0.32,fontSize:12.5,bold:true,color:INK,fontFace:B,isTextBox:true,margin:0});
tbl(s,[
 [hdr("회차"),hdr("시험 지진"),hdr("시험 행"),hdr("양성/음성"),hdr("BCE 대상 행")],
 ["1","2000 돗토리","24","15 / 9","101"],
 ["2","2004 니가타현주에쓰","10","8 / 2","115"],
 ["3","2016 구마모토","29","26 / 3","96"],
 ["4","2018 오사카","7","5 / 2","118"],
 ["5","2018 훗카이도","13","9 / 4","112"]],
 {x:0.7,y:4.1,w:6.6,colW:[0.7,2.6,1.0,1.2,1.1],rowH:0.32,fontSize:10.5,align:"center"});
s.addText("결과를 보기 전에 고정한 값",{x:7.6,y:3.68,w:5.05,h:0.32,fontSize:12.5,bold:true,color:INK,fontFace:B,isTextBox:true,margin:0});
tbl(s,[
 [hdr("항목"),hdr("값")],
 ["ω (주 조건)","4.35  ( = 418 ÷ 96 )"],
 ["ω (대조군 / 민감도)","0 / 1 / 10"],
 ["산지 변수","국세조사 mountain_ratio"],
 ["BCE 확률","prior q_LS (사후 아님)"],
 ["공변량","목조만 (산지 η는 회귀식에 없음)"],
 ["공통","3000 epoch · Adam lr 0.02 · λγ 10 · seed 0"]],
 {x:7.6,y:4.1,w:5.05,colW:[1.85,3.2],rowH:0.32,fontSize:10.5});
s.addText("음성이 없어 AUC가 정의되지 않는 4개 지진(2007·2008·2021·2024)은 매 회차 BCE에 포함한다. 가중평균은 24·10·29·7·13 ÷ 83.",
  {x:0.7,y:6.55,w:11.95,h:0.34,fontSize:10.5,color:MUTED,italic:true,fontFace:B,isTextBox:true,margin:0});
s.addNotes("시험 지진의 피해 건수는 NLL에 그대로 들어간다. 가리는 것은 그 지진의 ls_flag뿐이다.");

/* ───────────────────────── 5. 실행 조건 ───────────────────────── */
s=pres.addSlide(); s.background={color:WHITE};
title(s,"실행한 조건 — 총 30회","필수 14회 + 선택 10회 + 링크 민감도 6회. 모두 결과 확인 전에 정한 조건이다");
tbl(s,[
 [hdr("ID"),hdr("계열"),hdr("κ·m"),hdr("ω"),hdr("학습 파라미터 (LS prior)"),hdr("실행"),hdr("역할")],
 ["A0","A","없음","0","a, b","1","기존 재현 (기준선)"],
 ["A1","A","있음","0","a, b, κ","1","정답 없이 κ만 추가"],
 [{text:"A2",options:{bold:true,fill:{color:"F6E4E0"}}},{text:"A",options:{fill:{color:"F6E4E0"}}},{text:"있음",options:{fill:{color:"F6E4E0"}}},{text:"4.35",options:{bold:true,fill:{color:"F6E4E0"}}},{text:"a, b, κ",options:{fill:{color:"F6E4E0"}}},{text:"5",options:{bold:true,fill:{color:"F6E4E0"}}},{text:"교수님 제안",options:{bold:true,fill:{color:"F6E4E0"}}}],
 ["B0","B","없음","0","없음 (b = 0 고정)","1","면적 항 기준선"],
 ["B1","B","있음","0","b, κ","1","정답 없이 κ만 추가"],
 [{text:"B2",options:{bold:true,fill:{color:"F6E4E0"}}},{text:"B",options:{fill:{color:"F6E4E0"}}},{text:"있음",options:{fill:{color:"F6E4E0"}}},{text:"4.35",options:{bold:true,fill:{color:"F6E4E0"}}},{text:"b, κ",options:{fill:{color:"F6E4E0"}}},{text:"5",options:{bold:true,fill:{color:"F6E4E0"}}},{text:"제안 + 면적 항",options:{bold:true,fill:{color:"F6E4E0"}}}],
 ["B2-ω1 / B2-ω10","B","있음","1 / 10","b, κ","10","ω 민감도 (선택)"],
 ["B0-logit / B2-logit","B","없음 / 있음","0 / 4.35","b, κ","6","링크 민감도"]],
 {x:0.7,y:1.72,w:11.95,colW:[2.35,0.85,1.15,1.0,3.1,0.8,2.7],rowH:0.355,fontSize:10.5,align:"center"});
s.addShape(pres.ShapeType.roundRect,{x:0.7,y:5.3,w:5.85,h:1.42,rectRadius:0.09,fill:{color:SAND},line:{color:LINE,width:0.5}});
s.addText("링크를 log로 정한 이유",{x:0.98,y:5.5,w:5.3,h:0.3,fontSize:12,bold:true,color:INK,fontFace:H,isTextBox:true,margin:0});
s.addText("지시서는 logit, 기존 브랜치는 log였다. 둘 다 돌린 결과 LS는 순위가 완전히 같았고(0.8550 동일) LQ만 log가 앞서(0.7812 vs 0.7768, P=0.938) log를 주 조건으로 정했다.",
  {x:0.98,y:5.85,w:5.3,h:0.75,fontSize:10.5,color:MUTED,lineSpacing:14,fontFace:B,isTextBox:true,margin:0});
s.addShape(pres.ShapeType.roundRect,{x:6.8,y:5.3,w:5.85,h:1.42,rectRadius:0.09,fill:{color:SAND},line:{color:LINE,width:0.5}});
s.addText("사전등록을 지킨 방식",{x:7.08,y:5.5,w:5.3,h:0.3,fontSize:12,bold:true,color:INK,fontFace:H,isTextBox:true,margin:0});
s.addText("ω·라벨·산지 변수·판정 기준을 결과 확인 전에 고정했다. 결과를 보고 조건을 바꾸지 않았고, 추가로 떠오른 아이디어는 '사후 탐색'으로 분리했다.",
  {x:7.08,y:5.85,w:5.3,h:0.75,fontSize:10.5,color:MUTED,lineSpacing:14,fontFace:B,isTextBox:true,margin:0});
s.addNotes("A2와 B2가 교수님 제안을 그대로 구현한 조건이다. 나머지는 비교를 위한 기준선과 민감도다.");

/* ───────────────────────── 6. 검증 ───────────────────────── */
s=pres.addSlide(); s.background={color:WHITE};
title(s,"본 실험 전 검증","기존 결과를 재현하고, 새 옵션이 기존 계산을 건드리지 않는지 확인했다");
s.addText("기존 결과 재현 (A0)",{x:0.7,y:1.72,w:6,h:0.32,fontSize:13,bold:true,color:INK,fontFace:B,isTextBox:true,margin:0});
tbl(s,[
 [hdr("지표"),hdr("기준값"),hdr("재현값"),hdr("차이")],
 ["LS 사후 가중 AUC","0.7222","0.7222",{text:"0.0000",options:{color:SAGE,bold:true}}],
 ["LS prior 가중 AUC","0.7969","0.7969",{text:"0.0000",options:{color:SAGE,bold:true}}],
 ["LQ 사후 가중 AUC","0.7458","0.7458",{text:"0.0000",options:{color:SAGE,bold:true}}],
 ["LS MSE","0.3724","0.3724",{text:"0.0000",options:{color:SAGE,bold:true}}],
 ["면적 항 prior 단독","0.840","0.8400",{text:"0.0000",options:{color:SAGE,bold:true}}],
 ["면적 항 사후 (기존 자료)","0.855","0.8550",{text:"0.0000",options:{color:SAGE,bold:true}}]],
 {x:0.7,y:2.14,w:6.1,colW:[2.5,1.2,1.2,1.2],rowH:0.345,fontSize:10.5,align:"center"});
s.addText("데이터와 구현 점검",{x:7.2,y:1.72,w:5.45,h:0.32,fontSize:13,bold:true,color:INK,fontFace:B,isTextBox:true,margin:0});
[["ls_flag가 기존 학습 loss에 없음","train()에 정답을 넘기지 않는 것을 확인"],
 ["LS 평가 125행 = 양성 105 / 음성 20","AUC 정의 지진 5개, 가중치 합 83"],
 ["mountain_ratio 결측 없음","평가 125행 전부 값 존재"],
 ["면적 자료 결측 없음","USGS 엑셀 area_km2, 419행 전부 존재"],
 ["옵션을 끄면 기존과 완전히 동일","A0의 예측·파라미터가 수정 전과 diff 무차이"],
 ["κ가 optimizer에 포함됨","아니면 RuntimeError로 즉시 중단"],
 ["30회 전부 NaN·발산 없음","최종 loss < 초기 loss"]]
 .forEach(([t,d],i)=>{
  const y=2.16+i*0.62;
  s.addShape(pres.ShapeType.ellipse,{x:7.2,y:y+0.05,w:0.22,h:0.22,fill:{color:SAGE},line:{color:SAGE,width:0}});
  s.addText(t,{x:7.58,y:y,w:5.1,h:0.28,fontSize:11.5,bold:true,color:INK,fontFace:B,isTextBox:true,margin:0});
  s.addText(d,{x:7.58,y:y+0.26,w:5.1,h:0.26,fontSize:10,color:MUTED,fontFace:B,isTextBox:true,margin:0});
});
s.addText("다만 A1은 발표자료 12쪽 ③과 어긋났다 — LS 0.7479(기대 0.717), κ 0.2795(기대 0.05). 12쪽 ③이 κ를 어디에 어떤 m으로 넣었는지 확인이 필요하다. A2 판정은 A0 기준이라 영향받지 않는다.",
  {x:0.7,y:4.4,w:6.1,h:0.95,fontSize:10.5,color:TERRA,lineSpacing:14,fontFace:B,isTextBox:true,margin:0});
s.addNotes("A0 재현이 소수 넷째 자리까지 정확히 맞아, 이후 비교가 같은 기준 위에 있다는 것을 보장한다.");

/* ───────────────────────── 7. LS 결과 ───────────────────────── */
s=pres.addSlide(); s.background={color:WHITE};
title(s,"결과 ① 산사태(LS)","가린 지진으로만 채점한 사후 가중 AUC. 위로 갈수록 좋다");
s.addChart(pres.ChartType.bar,[{name:"LS 사후 가중 AUC",
  labels:["A0  기존 prior","A1  + κ·m","B1  면적 항 + κ·m","A2  제안 (A 계열)","B2-ω1","B2  제안 + 면적 항","B0  면적 항 기준선"],
  values:[0.7222,0.7479,0.7285,0.8039,0.8136,0.8507,0.8550]}],
  Object.assign({},chartFrame,{x:0.7,y:1.74,w:7.6,h:4.5,barDir:"bar",barGapWidthPct:45,
  chartColors:[TERRA],valAxisMinVal:0.65,valAxisMaxVal:0.90,valAxisMajorUnit:0.05,
  dataLabelPosition:"outEnd"}));
card(s,8.6,1.74,4.05,4.5);
s.addText("읽는 법",{x:8.9,y:1.96,w:3.5,h:0.3,fontSize:12.5,bold:true,color:INK,fontFace:H,isTextBox:true,margin:0});
[["A2가 A0을 크게 넘었다","0.7222 → 0.8039 (+0.0817)"],
 ["B2는 B0을 넘지 못했다","0.8550 → 0.8507 (−0.0044)"],
 ["1등은 학습을 안 한 B0","prior 학습 파라미터 0개"],
 ["B1이 최하위권","면적 항이 있어도 κ를 감독 없이 학습시키면 0.7285로 망가진다"]]
 .forEach(([t,d],i)=>{
  const y=2.4+i*0.95;
  s.addShape(pres.ShapeType.ellipse,{x:8.9,y:y+0.04,w:0.2,h:0.2,fill:{color:i===3?TERRA:SAGE},line:{color:i===3?TERRA:SAGE,width:0}});
  s.addText(t,{x:9.24,y:y-0.02,w:3.16,h:0.28,fontSize:11.5,bold:true,color:INK,fontFace:B,isTextBox:true,margin:0});
  s.addText(d,{x:9.24,y:y+0.26,w:3.16,h:0.52,fontSize:10.5,color:MUTED,lineSpacing:13,fontFace:B,isTextBox:true,margin:0});
});
s.addText("LS 평가 125행 중 AUC가 정의되는 5개 지진 83행. 음성은 20개뿐이라 구간이 넓다.",
  {x:0.7,y:6.42,w:11.95,h:0.32,fontSize:10.5,color:MUTED,italic:true,fontFace:B,isTextBox:true,margin:0});
s.addNotes("B0은 산사태 정답을 한 번도 쓰지 않았고 prior에 학습 파라미터가 없는데도 1등이다.");

/* ───────────────────────── 8. 판정 ───────────────────────── */
s=pres.addSlide(); s.background={color:WHITE};
title(s,"판정","성공 조건도 결과를 보기 전에 고정했다 — 기준선 초과 + P(차이>0) ≥ 95% + κ 부호 일치");
s.addShape(pres.ShapeType.roundRect,{x:0.7,y:1.74,w:5.85,h:2.35,rectRadius:0.09,fill:{color:"EDF2EE"},line:{color:SAGE,width:1.25}});
s.addText("A2  성공",{x:1.0,y:1.95,w:3.0,h:0.45,fontSize:22,bold:true,color:SAGE,fontFace:H,isTextBox:true,margin:0});
s.addText("교수님 제안 · A 계열",{x:1.0,y:2.42,w:5.25,h:0.28,fontSize:11,color:MUTED,fontFace:B,isTextBox:true,margin:0});
[["가중 AUC","0.8039  >  A0 0.7222"],["P(차이 > 0)","0.9813  ≥  0.95"],["κ 부호","5회차 전부 양수 (+0.93 ~ +1.37)"]]
 .forEach(([k,v],i)=>{
  s.addText(k,{x:1.0,y:2.8+i*0.4,w:1.5,h:0.3,fontSize:11,color:MUTED,fontFace:B,isTextBox:true,margin:0});
  s.addText(v,{x:2.55,y:2.8+i*0.4,w:3.7,h:0.3,fontSize:11.5,bold:true,color:INK,fontFace:B,isTextBox:true,margin:0});
});
s.addShape(pres.ShapeType.roundRect,{x:6.8,y:1.74,w:5.85,h:2.35,rectRadius:0.09,fill:{color:"F9EAE7"},line:{color:TERRA,width:1.25}});
s.addText("B2  실패",{x:7.1,y:1.95,w:3.0,h:0.45,fontSize:22,bold:true,color:TERRA,fontFace:H,isTextBox:true,margin:0});
s.addText("제안 + 면적 항 · B 계열",{x:7.1,y:2.42,w:5.25,h:0.28,fontSize:11,color:MUTED,fontFace:B,isTextBox:true,margin:0});
[["가중 AUC","0.8507  ≤  B0 0.8550"],["P(차이 > 0)","0.0000"],["κ 부호","4회 음수 / 1회 양수 — 뒤집힘"]]
 .forEach(([k,v],i)=>{
  s.addText(k,{x:7.1,y:2.8+i*0.4,w:1.5,h:0.3,fontSize:11,color:MUTED,fontFace:B,isTextBox:true,margin:0});
  s.addText(v,{x:8.65,y:2.8+i*0.4,w:3.7,h:0.3,fontSize:11.5,bold:true,color:INK,fontFace:B,isTextBox:true,margin:0});
});
s.addText("짝지은 부트스트랩 3,000회 (seed 0) — 지진 안에서 양성·음성을 따로 복원추출, 모든 조건이 같은 표본",
  {x:0.7,y:4.3,w:11.95,h:0.3,fontSize:12,bold:true,color:INK,fontFace:B,isTextBox:true,margin:0});
tbl(s,[
 [hdr("비교"),hdr("차이 (관측)"),hdr("95% 구간"),hdr("P(차이 > 0)"),hdr("해석")],
 [{text:"A2 − A0",options:{bold:true}},"+0.0817","[+0.0031, +0.1644]",{text:"0.9813",options:{bold:true,color:SAGE}},"제안이 기존 prior를 유의하게 개선"],
 ["A2 − A1","+0.0560","[+0.0004, +0.1246]",{text:"0.9763",options:{color:SAGE}},"정답을 쓴 쪽이 안 쓴 쪽보다 낫다"],
 [{text:"B2 − B0",options:{bold:true}},"−0.0044","[−0.0261, 0.0000]",{text:"0.0000",options:{bold:true,color:TERRA}},"재표본 3,000벌 전부에서 못 넘음"],
 ["B2 − B1","+0.1222","[+0.0514, +0.1981]",{text:"1.0000",options:{color:SAGE}},"감독이 있으면 κ 폭주는 막힌다"],
 ["B2 − A2","+0.0468","[−0.0287, +0.1322]","0.8860","면적 항이 앞서지만 구간은 0을 걸침"]],
 {x:0.7,y:4.7,w:11.95,colW:[1.5,1.5,2.2,1.4,5.35],rowH:0.335,fontSize:10.5,align:"center"});
s.addNotes("B2−B1이 P=1.0인 것이 중요하다. 감독을 붙이면 κ가 폭주하는 것은 막아준다. 다만 그래봐야 아무것도 안 넣은 B0을 못 넘는다.");

/* ───────────────────────── 9. 성분 분해 ───────────────────────── */
s=pres.addSlide(); s.background={color:WHITE};
title(s,"왜 그런가 ① 면적 항이 산지 정보를 이미 담고 있다","회귀를 거치지 않은 prior 점수만으로 잰 가중 AUC");
s.addChart(pres.ChartType.bar,[
 {name:"LS",labels:["USGS π 단독","시정촌 면적 log k 단독","산지 비율 단독","π + 면적 항"],values:[0.7969,0.8214,0.8060,0.8400]},
 {name:"LQ",labels:["USGS π 단독","시정촌 면적 log k 단독","산지 비율 단독","π + 면적 항"],values:[0.7154,0.5470,0.4287,0.7698]}],
 Object.assign({},chartFrame,{x:0.7,y:1.76,w:7.5,h:3.5,barDir:"col",barGapWidthPct:55,
 chartColors:[TERRA,SAGE],showLegend:true,legendPos:"t",legendColor:MUTED,legendFontSize:11,
 valAxisMinVal:0.35,valAxisMaxVal:0.90,valAxisMajorUnit:0.1,dataLabelPosition:"outEnd",dataLabelFontSize:9.5}));
card(s,8.5,1.76,4.15,3.5);
s.addText("두 가지가 보인다",{x:8.8,y:1.98,w:3.6,h:0.3,fontSize:12.5,bold:true,color:INK,fontFace:H,isTextBox:true,margin:0});
s.addText("① LS에서는 시정촌 면적만으로도 0.8214가 나온다. USGS 확률값(0.7969)보다 높다.\n\n② 그런데 LQ에서는 면적 단독이 0.5470으로 우연 수준이다. 그런데도 π와 더하면 0.7154 → 0.7698로 오른다.",
  {x:8.8,y:2.38,w:3.6,h:1.6,fontSize:11,color:MUTED,lineSpacing:15,fontFace:B,isTextBox:true,margin:0});
s.addText("면적이 라벨을 직접 켜는 것이 아니라, λ = π × k 라는 유도식이 실제로 작동한다는 뜻이다.",
  {x:8.8,y:4.2,w:3.6,h:0.85,fontSize:11,bold:true,color:TERRA,lineSpacing:15,fontFace:B,isTextBox:true,margin:0});
s.addShape(pres.ShapeType.roundRect,{x:0.7,y:5.42,w:11.95,h:1.25,rectRadius:0.09,fill:{color:DARK},line:{color:DARK,width:0}});
s.addText("산지 비율과 시정촌 면적의 상관 = 0.53",{x:1.0,y:5.6,w:5.4,h:0.34,fontSize:14,bold:true,color:TERRA,fontFace:H,isTextBox:true,margin:0});
s.addText("두 변수가 같은 것(산이 얼마나 넓게 있는가)을 다른 방식으로 재고 있다. 실제로 A2가 정답을 배워 도달한 prior(0.8341)가 면적 항이 구조만으로 얻은 prior(0.8400)와 거의 같은 자리다 — 서로 다른 길로 같은 정보에 닿았다.",
  {x:1.0,y:6.0,w:11.35,h:0.55,fontSize:11.5,color:"CFC4BC",lineSpacing:15,fontFace:B,isTextBox:true,margin:0});
s.addNotes("LQ에서 면적 단독이 무력하다는 점이 중요하다. 'LS 결과는 시정촌이 크면 라벨이 켜지는 아티팩트 아닌가'라는 의심에 대한 반증이다.");

/* ───────────────────────── 10. B2 실패 이유 ───────────────────────── */
s=pres.addSlide(); s.background={color:WHITE};
title(s,"왜 그런가 ② κ가 순위가 아니라 확률 수준을 고치는 데 쓰였다","회차별로 학습된 κ와, 그 원인이 된 2018 훗카이도");
s.addText("회차별 κ",{x:0.7,y:1.72,w:5.3,h:0.3,fontSize:12.5,bold:true,color:INK,fontFace:B,isTextBox:true,margin:0});
tbl(s,[
 [hdr("시험 지진"),hdr("A2  κ"),hdr("B2  κ")],
 ["2000 돗토리",{text:"+0.9356",options:{color:SAGE}},{text:"−0.0254",options:{color:TERRA}}],
 ["2004 니가타현주에쓰",{text:"+0.9259",options:{color:SAGE}},{text:"−0.1898",options:{color:TERRA}}],
 ["2016 구마모토",{text:"+1.3698",options:{color:SAGE}},{text:"−0.4070",options:{color:TERRA}}],
 ["2018 오사카",{text:"+1.0417",options:{color:SAGE}},{text:"−0.2655",options:{color:TERRA}}],
 ["2018 훗카이도",{text:"+0.9871",options:{color:SAGE}},{text:"+0.1583",options:{color:GOLD,bold:true}}]],
 {x:0.7,y:2.12,w:5.3,colW:[2.7,1.3,1.3],rowH:0.36,fontSize:11,align:"center"});
s.addText("강제로 κ = +1을 넣으면 prior가 0.8400 → 0.8539로 오른다. 학습된 κ(−0.41)는 순위를 최대화하는 방향의 반대로 갔다.",
  {x:0.7,y:4.35,w:5.3,h:0.75,fontSize:11,color:TERRA,lineSpacing:15,fontFace:B,isTextBox:true,margin:0});
s.addText("2018 훗카이도 — 산이 많은 곳이 오히려 음성이다",{x:6.35,y:1.72,w:6.3,h:0.3,fontSize:12.5,bold:true,color:INK,fontFace:B,isTextBox:true,margin:0});
tbl(s,[
 [hdr("시정촌"),hdr("산사태"),hdr("산지 z"),hdr("q 변화 (B0→B2)")],
 [{text:"히다카초 (日高町)",options:{bold:true}},{text:"없음",options:{color:TERRA,bold:true}},"+0.99","0.9706 → 0.9730"],
 [{text:"유바리시 (夕張市)",options:{bold:true}},{text:"없음",options:{color:TERRA,bold:true}},"+1.35","0.9612 → 0.9663"],
 ["기타히로시마시 (北広島市)",{text:"있음",options:{color:SAGE}},"−0.57","0.6641 → 0.6290"],
 ["유니초 (由仁町)",{text:"있음",options:{color:SAGE}},"−0.63","0.8282 → 0.8039"]],
 {x:6.35,y:2.12,w:6.3,colW:[2.5,0.95,1.05,1.8],rowH:0.42,fontSize:10.5,align:"center"});
s.addText("면적 항 prior는 q가 이미 0.94~0.99로 포화돼 있다. 이 상태에서 BCE를 가장 빨리 줄이는 길은 과신한 행을 끌어내리는 것인데, 거짓양성이 전부 산 많은 곳이다. 그래서 κ가 음수로 간다 — 순위 개선이 아니라 수준 보정이다.",
  {x:6.35,y:4.1,w:6.3,h:1.0,fontSize:11,color:MUTED,lineSpacing:15,fontFace:B,isTextBox:true,margin:0});
s.addShape(pres.ShapeType.roundRect,{x:0.7,y:5.35,w:11.95,h:1.3,rectRadius:0.09,fill:{color:SAND},line:{color:LINE,width:0.5}});
s.addText("결정적 확인 — 가려둔 83행에서 잰 BCE (자기 목적함수인데도 일반화되지 않는다)",
  {x:1.0,y:5.55,w:11.35,h:0.3,fontSize:12,bold:true,color:INK,fontFace:H,isTextBox:true,margin:0});
s.addText("B0 = 0.4322   ·   B2 (ω=4.35) = 0.4548   ·   B2-ω10 = 0.4599   →  정답으로 학습한 조건이 학습하지 않은 조건보다 나쁘다",
  {x:1.0,y:5.95,w:11.35,h:0.55,fontSize:12,color:MUTED,lineSpacing:16,fontFace:B,isTextBox:true,margin:0});
s.addNotes("훗카이도 회차만 κ가 양수인 것은, 그 회차에서만 훗카이도의 반대되는 라벨이 BCE에서 빠지기 때문이다. κ 부호 불안정의 원인은 학습이 아니라 이 지진 하나다.");

/* ───────────────────────── 11. LQ 결과 ───────────────────────── */
s=pres.addSlide(); s.background={color:WHITE};
title(s,"결과 ② 액상화(LQ)","LQ는 음성이 120개로 LS(20개)보다 6배 많아 그 자체로 더 튼튼한 평가판이다");
s.addChart(pres.ChartType.bar,[{name:"LQ 사후 가중 AUC",
  labels:["A1","A0","A2","B1","B2","B0","C0  (사후 탐색)"],
  values:[0.7454,0.7458,0.7590,0.7796,0.7806,0.7812,0.8158]}],
 Object.assign({},chartFrame,{x:0.7,y:1.76,w:7.5,h:3.3,barDir:"col",barGapWidthPct:50,
 chartColors:[SAGE,SAGE,SAGE,TERRA,TERRA,TERRA,DARK],varyColors:true,
 valAxisMinVal:0.70,valAxisMaxVal:0.84,valAxisMajorUnit:0.03,dataLabelPosition:"outEnd",dataLabelFontSize:10}));
card(s,8.5,1.76,4.15,3.3);
s.addText("LQ는 학습 파라미터가 없다",{x:8.8,y:1.98,w:3.6,h:0.3,fontSize:12.5,bold:true,color:INK,fontFace:H,isTextBox:true,margin:0});
s.addText("z_LQ = log(π_LQ) + log k_LQ 뿐이고 b_LQ는 0으로 고정, κ도 없다. BCE도 LS에만 걸린다.\n\n그래서 B 계열의 LQ 개선(0.7458 → 0.7812)은 순수하게 면적 항이라는 구조만으로 얻은 것이다.",
  {x:8.8,y:2.38,w:3.6,h:1.7,fontSize:11,color:MUTED,lineSpacing:15,fontFace:B,isTextBox:true,margin:0});
s.addText("다만 조건 간 차이는 LS만큼 결정적이지 않다. B0 − A0의 95% 구간이 0을 걸친다 (P = 0.892).",
  {x:8.8,y:4.2,w:3.6,h:0.75,fontSize:10.5,color:TERRA,lineSpacing:14,fontFace:B,isTextBox:true,margin:0});
s.addText("주의 — 이득이 어디서 오는지 쪼개 보면",{x:0.7,y:5.22,w:11.95,h:0.3,fontSize:12,bold:true,color:INK,fontFace:B,isTextBox:true,margin:0});
tbl(s,[
 [hdr("조건"),hdr("전체 6개 지진 (가중 182)"),hdr("음성 22~31개인 3개 (144)"),hdr("음성 1~3개인 3개 (38)")],
 ["A0","0.7458","0.8329","0.4156"],
 ["A2","0.7590",{text:"0.8437",options:{bold:true}},"0.4379"],
 ["B0","0.7812","0.8406","0.5350"]],
 {x:0.7,y:5.54,w:11.95,colW:[1.5,3.5,3.5,3.45],rowH:0.3,fontSize:10.5,align:"center"});
s.addText("믿을 만한 3개 지진만 보면 A2(0.8437)와 B0(0.8406)이 사실상 동률이다. B0의 LQ 우위는 음성이 1개뿐인 지진 두 개에서 나온다.",
  {x:0.7,y:6.78,w:11.95,h:0.3,fontSize:10.5,color:MUTED,italic:true,fontFace:B,isTextBox:true,margin:0});
s.addNotes("LQ는 표본이 튼튼하지만, 조건 간 차이는 LS만큼 크지 않다. 정직하게 쪼개 보면 B0의 우위는 노이즈가 큰 소규모 지진에서 나온다.");

/* ───────────────────────── 12. 사후 탐색 ───────────────────────── */
s=pres.addSlide(); s.background={color:WHITE};
title(s,"사후 탐색 — b_LQ 고정을 풀면","사전등록 조건표 밖의 실험이며 판정 대상이 아니다");
s.addShape(pres.ShapeType.roundRect,{x:0.7,y:1.72,w:11.95,h:0.95,rectRadius:0.09,fill:{color:SAND},line:{color:LINE,width:0.5}});
s.addText("문제 — log k_LQ의 평균이 6.7쯤이라 q_LQ가 통째로 밀려 올라간다. 중앙값 0.9188인데 실제 LQ 발생률은 229행 중 0.476이다. b_LQ가 0으로 고정돼 수준을 잡을 수단이 없었다.",
  {x:1.0,y:1.92,w:11.35,h:0.6,fontSize:12,color:INK,lineSpacing:16,fontFace:B,isTextBox:true,margin:0});
const comp=[["LQ 사전 가중 AUC","0.7698","0.7698","변화 없음 (예측대로)",false],
            ["LQ 사후 가중 AUC","0.7812","0.8158","+0.0346",true],
            ["LQ MSE (사후)","0.2497","0.2399","−0.0098",true],
            ["LQ BCE (사전)","0.8760","0.7257","−0.1503",true],
            ["q_LQ 중앙값","0.9145","0.1485","실제 발생률 0.476",false],
            ["LS 사전 가중 AUC","0.8400","0.8400","완전히 동일 (0.00e+00)",false],
            ["LS 사후 가중 AUC","0.8550","0.8529","−0.0021",false]];
tbl(s,[[hdr("지표"),hdr("B0  (b_LQ = 0 고정)"),hdr("C0  (b_LQ 학습, b_LQ = −4.12)"),hdr("변화")]]
 .concat(comp.map(r=>[r[0],r[1],{text:r[2],options:{bold:true}},
   {text:r[3],options:{color:r[4]?SAGE:MUTED,bold:r[4]}}])),
 {x:0.7,y:2.86,w:8.0,colW:[2.15,1.95,2.25,1.65],rowH:0.355,fontSize:10.5,align:"center"});
card(s,8.95,2.86,3.7,2.85);
s.addText("왜 순위는 그대로인가",{x:9.23,y:3.06,w:3.15,h:0.3,fontSize:12.5,bold:true,color:INK,fontFace:H,isTextBox:true,margin:0});
s.addText("b_LQ는 모든 행에 더해지는 같은 상수다. 상수를 더해도 순위는 바뀌지 않으므로 prior AUC가 0.7698 그대로다.\n\n그런데 4상태 가중치가 제대로 잡히면서 사후 AUC가 올랐다. 확률 수준만 고쳤는데 사후 순위가 좋아진 것이다.",
  {x:9.23,y:3.46,w:3.15,h:2.1,fontSize:11,color:MUTED,lineSpacing:15,fontFace:B,isTextBox:true,margin:0});
s.addShape(pres.ShapeType.roundRect,{x:0.7,y:6.1,w:8.0,h:0.8,rectRadius:0.09,fill:{color:DARK},line:{color:DARK,width:0}});
s.addText("짝지은 부트스트랩 3,000회 — C0 − B0 = +0.0342,  95% 구간 [+0.0009, +0.0698],  P(차이 > 0) = 0.978",
  {x:1.0,y:6.3,w:7.4,h:0.42,fontSize:11,bold:true,color:WHITE,fontFace:B,isTextBox:true,margin:0});
s.addNotes("결과를 보고 나온 아이디어이므로 판정표에 섞지 않고 별도 파일로 분리했다. 다만 예측이 명확했고 그대로 맞았다.");

/* ─────────────── 12-2. log k 중심화 ─────────────── */
s=pres.addSlide(); s.background={color:WHITE};
title(s,"매개변수화 점검 — log k에서 평균을 뺄 것인가","b를 학습하는 채널에서만 뺀다. b를 고정한 채널에서 빼면 유도식이 깨진다");
s.addShape(pres.ShapeType.roundRect,{x:0.7,y:1.7,w:5.85,h:1.5,rectRadius:0.09,fill:{color:"EDF2EE"},line:{color:SAGE,width:1.25}});
s.addText("b를 학습하는 채널 → 뺀다",{x:1.0,y:1.9,w:5.3,h:0.32,fontSize:13,bold:true,color:SAGE,fontFace:H,isTextBox:true,margin:0});
s.addText("b가 '평균 크기 시정촌에서의 log-odds'라는 뜻을 갖고, b와 log k의 상관이 줄어 최적화가 안정된다.",
  {x:1.0,y:2.3,w:5.3,h:0.75,fontSize:11.5,color:MUTED,lineSpacing:15,fontFace:B,isTextBox:true,margin:0});
s.addShape(pres.ShapeType.roundRect,{x:6.8,y:1.7,w:5.85,h:1.5,rectRadius:0.09,fill:{color:"F9EAE7"},line:{color:TERRA,width:1.25}});
s.addText("b = 0 고정인 채널 → 빼면 안 된다",{x:7.1,y:1.9,w:5.3,h:0.32,fontSize:13,bold:true,color:TERRA,fontFace:H,isTextBox:true,margin:0});
s.addText("재매개변수화가 아니라 다른 모형이 된다. 안 뺀 z = log(π̄ · k) = log λ 가 유도식 그 자체다. B0이 여기 해당한다.",
  {x:7.1,y:2.3,w:5.3,h:0.75,fontSize:11.5,color:MUTED,lineSpacing:15,fontFace:B,isTextBox:true,margin:0});
s.addText("확인 — b 상자를 [−12, 20]으로 똑같이 열고 센터링 유/무를 비교했다",
  {x:0.7,y:3.36,w:11.95,h:0.3,fontSize:12.5,bold:true,color:INK,fontFace:B,isTextBox:true,margin:0});
tbl(s,[
 [hdr("조건"),hdr("센터링"),hdr("뺀 값 off_LS / off_LQ"),hdr("b_LS 유효수준"),hdr("b_LQ 유효수준"),hdr("κ"),hdr("LS 사후"),hdr("LQ 사후")],
 ["B1","한다","8.0422 / 0","−2.4362","0","−0.8395","0.7285","0.7796"],
 ["B1","안 한다","0 / 0","−2.4309","0","−0.8386","0.7285","0.7796"],
 ["C0","한다","0 / 6.6559","0","−4.1139","—","0.8529","0.8158"],
 ["C0","안 한다","0 / 0","0","−4.1186","—","0.8529","0.8158"],
 ["B2","한다","8.0422 / 0","−0.2946","0","−0.1462","0.8507","0.7807"],
 ["B2","안 한다","0 / 0","−0.2955","0","−0.1461","0.8507","0.7806"]],
 {x:0.7,y:3.76,w:11.95,colW:[1.0,1.15,2.5,1.85,1.85,1.3,1.15,1.15],rowH:0.335,fontSize:10.5,align:"center"});
s.addShape(pres.ShapeType.roundRect,{x:0.7,y:5.88,w:11.95,h:1.0,rectRadius:0.09,fill:{color:DARK},line:{color:DARK,width:0}});
s.addText("최적해는 같다 — 소수 셋째 자리까지 일치한다. 차이는 b의 해석과 조건수뿐이다.",
  {x:1.0,y:6.05,w:11.35,h:0.32,fontSize:13,bold:true,color:TERRA,fontFace:H,isTextBox:true,margin:0});
s.addText("단, 상자를 함께 열어야 한다. 기존 상자 [−2, 4]는 실제로 걸리고 있었고(B1의 b_LS가 하한 −2에 붙음), 센터링하면 LS는 b가 +8.21까지 가야 하는데 상한 4에 닿지 못한다.",
  {x:1.0,y:6.42,w:11.35,h:0.34,fontSize:11,color:"CFC4BC",fontFace:B,isTextBox:true,margin:0});
s.addNotes("센터링은 성능을 바꾸는 장치가 아니라 해석과 수치 안정성을 위한 매개변수화 선택이다. 상자가 걸리지 않는다는 전제에서만 최적해가 같다.");

/* ───────────────────────── 13. 권고 ───────────────────────── */
s=pres.addSlide(); s.background={color:DARK};
s.addText("결론 — 지금 가장 좋은 구성",{x:0.85,y:0.6,w:11.6,h:0.6,fontSize:32,bold:true,color:WHITE,fontFace:H,isTextBox:true,margin:0});
s.addText("두 가지를 나란히 제시한다. 사전등록 기준 1위와, 사후 탐색까지 포함한 1위다.",
  {x:0.85,y:1.26,w:11.6,h:0.34,fontSize:13,color:"A99A92",fontFace:B,isTextBox:true,margin:0});
s.addShape(pres.ShapeType.roundRect,{x:0.85,y:1.82,w:5.7,h:3.85,rectRadius:0.09,fill:{color:"3B2E2A"},line:{color:TERRA,width:1.5}});
s.addText("B0   사전등록 기준 1위",{x:1.15,y:2.02,w:5.1,h:0.36,fontSize:16,bold:true,color:TERRA,fontFace:H,isTextBox:true,margin:0});
s.addText("z_LS = log(π̄_LS) + log k_LS\nz_LQ = log(π̄_LQ) + log k_LQ\nκ 없음 · ω = 0 · b 전부 0 고정",
  {x:1.15,y:2.46,w:5.1,h:1.0,fontSize:12,color:WHITE,lineSpacing:18,fontFace:B,isTextBox:true,margin:0});
[["LS 사전 가중","0.8400"],["LS 사후 가중","0.8550"],["LQ 사전 가중","0.7698"],
 ["LQ 사후 가중","0.7812"],["LS MSE (사후)","0.1343"],["prior 학습 파라미터","0개"]]
 .forEach(([k,v],i)=>{
  s.addText(k,{x:1.15,y:3.52+i*0.345,w:2.9,h:0.3,fontSize:11,color:"A99A92",fontFace:B,isTextBox:true,margin:0});
  s.addText(v,{x:4.2,y:3.52+i*0.345,w:2.1,h:0.3,fontSize:12,bold:true,color:WHITE,align:"right",fontFace:B,isTextBox:true,margin:0});
});
s.addShape(pres.ShapeType.roundRect,{x:6.95,y:1.82,w:5.5,h:3.85,rectRadius:0.09,fill:{color:"3B2E2A"},line:{color:SAGE,width:1.5}});
s.addText("C0   사후 탐색 포함 1위",{x:7.25,y:2.02,w:4.9,h:0.36,fontSize:16,bold:true,color:"8FB8A2",fontFace:H,isTextBox:true,margin:0});
s.addText("B0과 같되 b_LQ만 학습한다 (−4.12로 수렴)\nLS 식은 B0과 글자 하나 다르지 않다\n→ LS 사전확률 최대 절대차 0.00e+00",
  {x:7.25,y:2.46,w:4.9,h:1.0,fontSize:12,color:WHITE,lineSpacing:18,fontFace:B,isTextBox:true,margin:0});
[["LS 사전 가중","0.8400"],["LS 사후 가중","0.8529"],["LQ 사전 가중","0.7698"],
 ["LQ 사후 가중","0.8158"],["LS MSE (사후)","0.1338"],["prior 학습 파라미터","1개"]]
 .forEach(([k,v],i)=>{
  s.addText(k,{x:7.25,y:3.52+i*0.345,w:2.8,h:0.3,fontSize:11,color:"A99A92",fontFace:B,isTextBox:true,margin:0});
  s.addText(v,{x:10.1,y:3.52+i*0.345,w:2.05,h:0.3,fontSize:12,bold:true,color:(i===3||i===4)?"8FB8A2":WHITE,align:"right",fontFace:B,isTextBox:true,margin:0});
});
s.addText("발표에서는 B0을 주 결과로 두고, A2는 '제안하신 LOEO 절차는 A 계열에서 유의하게 작동했으나(+0.0817, P=0.98), 면적 항이 이미 같은 정보를 담고 있어 B 계열에서는 추가 이득이 없었다'로 방법 검증 결과에 배치하는 것을 권한다. C0은 다음 실험 제안으로 붙인다.",
  {x:0.85,y:5.92,w:11.6,h:0.95,fontSize:11.5,color:"CFC4BC",lineSpacing:16,fontFace:B,isTextBox:true,margin:0});
s.addNotes("가장 좋은 결과가 가장 적게 학습한 구성이라는 점이 이번 실험의 핵심 메시지다.");

/* ───────────────────────── 14. 한계와 다음 ───────────────────────── */
s=pres.addSlide(); s.background={color:WHITE};
title(s,"한계와 다음 단계","숫자를 어디까지 믿을 수 있는지부터 적는다");
s.addText("한계",{x:0.7,y:1.72,w:5.85,h:0.3,fontSize:13,bold:true,color:TERRA,fontFace:B,isTextBox:true,margin:0});
[["LS 음성이 20개뿐이다","지진 안 양성–음성 쌍이 전부 합쳐 275쌍이다. 2018 오사카의 1.0000은 10쌍짜리다."],
 ["최고 기록은 새 값이 아니다","B0의 0.8550은 기존 자료의 0.855와 같다. 이번 실험에서 그것을 넘은 조건은 없었다."],
 ["A1이 발표자료 12쪽 ③과 어긋난다","LS 0.7479(기대 0.717), κ 0.2795(기대 0.05). 확인이 필요하다."],
 ["훗카이도 라벨을 다시 볼 필요가 있다","히다카초·유바리시의 ls_flag=0이 '없음'인지 '집계 항목 없음'인지 원자료 확인."]]
 .forEach(([t,d],i)=>{
  const y=2.12+i*1.1;
  card(s,0.7,y,5.85,0.98);
  s.addShape(pres.ShapeType.ellipse,{x:0.96,y:y+0.17,w:0.2,h:0.2,fill:{color:TERRA},line:{color:TERRA,width:0}});
  s.addText(t,{x:1.3,y:y+0.13,w:5.0,h:0.28,fontSize:11.5,bold:true,color:INK,fontFace:B,isTextBox:true,margin:0});
  s.addText(d,{x:1.3,y:y+0.42,w:5.0,h:0.5,fontSize:10.5,color:MUTED,lineSpacing:13,fontFace:B,isTextBox:true,margin:0});
});
s.addText("다음 단계",{x:6.8,y:1.72,w:5.85,h:0.3,fontSize:13,bold:true,color:SAGE,fontFace:B,isTextBox:true,margin:0});
[["병목은 prior가 아니라 우도다","A0은 prior 0.7969 → 사후 0.7222로 깎인다. 어느 피해 채널이 LS 순위를 망치는지 채널별로 끄고 재본다."],
 ["b_LQ 건을 정식 조건으로 사전등록","이번에는 사후 탐색으로만 확인했다. 조건을 미리 고정하고 다시 돌린다."],
 ["B에서 κ를 쓰려면 부호 제약(κ ≥ 0)","강제 κ=+1이 prior를 0.8539로 올린다. 다만 결과를 보고 나온 가설이라 별도 사전등록이 필요하다."],
 ["감독 대상을 산지 말고 다른 변수로","면적 항이 아직 모르는 정보 — 경사도, 지질, 강우 — 쪽이어야 한다."]]
 .forEach(([t,d],i)=>{
  const y=2.12+i*1.1;
  card(s,6.8,y,5.85,0.98);
  num(s,7.0,y+0.28,i+1,SAGE);
  s.addText(t,{x:7.62,y:y+0.13,w:4.85,h:0.28,fontSize:11.5,bold:true,color:INK,fontFace:B,isTextBox:true,margin:0});
  s.addText(d,{x:7.62,y:y+0.42,w:4.85,h:0.5,fontSize:10.5,color:MUTED,lineSpacing:13,fontFace:B,isTextBox:true,margin:0});
});
s.addText("산출물 — results/loeo/LOEO_결과.xlsx (요약·회차별·이벤트별·부트스트랩·재현·실행기록 7시트) · results/posthoc/사후탐색_결과.xlsx · 브랜치 claude/vigilant-wozniak-atum1b",
  {x:0.7,y:6.64,w:11.95,h:0.34,fontSize:10,color:MUTED,italic:true,fontFace:B,isTextBox:true,margin:0});
s.addNotes("한계를 먼저 적는 것이 중요하다. 특히 음성 20개라는 표본 제약은 모든 LS 숫자에 걸린다.");

pres.writeFile({fileName: process.argv[2] || "LOEO_발표자료.pptx"}).then(f=>console.log("작성:",f));
