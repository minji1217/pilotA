const pptxgen = require("pptxgenjs");
const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE";
pres.title = "면적항과 LOEO 실험";
pres.author = "Pilot A";

const DARK="16212A", DARK2="22313C", ACC="1D4E6B", ACC_L="4E7E9B", SOFT="E4EDF2",
      POS="2F7150", POS_L="7FB79A", NEG="A8442E", SURF="EDF1F3", LINE="D6DEE3",
      MUT="6B7A84", INK="16212A", WHT="FFFFFF", DIM="9AA9B2";
const H="Cambria", B="Calibri";

const title=(s,t,sub)=>{
  s.addText(t,{x:0.65,y:0.42,w:12.0,h:0.58,fontSize:32,bold:true,color:INK,fontFace:H,isTextBox:true,margin:0});
  if(sub) s.addText(sub,{x:0.65,y:1.02,w:12.0,h:0.4,fontSize:13,color:MUT,fontFace:B,isTextBox:true,margin:0});
};
const card=(s,x,y,w,h,fill,line)=>s.addShape(pres.ShapeType.roundRect,{x,y,w,h,rectRadius:0.08,
  fill:{color:fill||SURF},line:{color:line||LINE,width:line?1.25:0.5}});
const num=(s,x,y,n,c)=>{
  s.addShape(pres.ShapeType.ellipse,{x,y,w:0.4,h:0.4,fill:{color:c||ACC},line:{color:c||ACC,width:0}});
  s.addText(String(n),{x,y,w:0.4,h:0.4,fontSize:14,bold:true,color:WHT,align:"center",valign:"middle",fontFace:H,isTextBox:true,margin:0});
};
const tbl=(s,rows,opt)=>s.addTable(rows,Object.assign({
  border:{type:"solid",color:LINE,pt:0.5},fontFace:B,fontSize:10.5,color:INK,valign:"middle",autoPage:false},opt));
const hd=t=>({text:t,options:{bold:true,color:WHT,fill:{color:DARK},fontSize:9.5,align:"center"}});
const hl=t=>({text:t,options:{bold:true,color:WHT,fill:{color:DARK},fontSize:9.5,align:"left"}});
const g=(t)=>({text:t,options:{color:MUT}});
const bd=(t,c)=>({text:t,options:{bold:true,color:c||INK}});

/* ── 1 표지 ── */
let s=pres.addSlide(); s.background={color:DARK};
s.addText("파일럿 A · 후속실험 3",{x:0.85,y:1.42,w:8,h:0.32,fontSize:12.5,color:ACC_L,bold:true,charSpacing:2,fontFace:B,isTextBox:true,margin:0});
s.addText("면적항과 LOEO 실험",{x:0.85,y:1.88,w:8.3,h:1.0,fontSize:44,bold:true,color:WHT,fontFace:H,isTextBox:true,margin:0});
s.addText("USGS 값에 시정촌 면적 항을 넣고, 산사태 정답을 학습에도 쓰되\n지진을 하나씩 가려 평가했다",
  {x:0.85,y:3.0,w:8.3,h:0.8,fontSize:15,color:"C3CFD6",lineSpacing:24,fontFace:B,isTextBox:true,margin:0});
s.addShape(pres.ShapeType.line,{x:0.85,y:4.0,w:2.8,h:0,line:{color:ACC_L,width:2.5}});
s.addText("사전등록 30회 + 사후 탐색 30회 · LOEO 5회차\n부트스트랩 3,000회 · seed 0 · 3000 epoch · Adam lr 0.02 · λγ 10",
  {x:0.85,y:4.22,w:8.3,h:0.8,fontSize:12,color:"8B9BA6",lineSpacing:19,fontFace:B,isTextBox:true,margin:0});
[["0.8550","최고 LS 가중 AUC"],["0개","그 조건의 사전 학습 파라미터"],["60회","전체 학습 실행"]].forEach(([v,l],i)=>{
  const y=1.55+i*1.55;
  s.addShape(pres.ShapeType.roundRect,{x:9.7,y,w:2.95,h:1.3,rectRadius:0.08,fill:{color:DARK2},line:{color:"31424F",width:0.75}});
  s.addText(v,{x:9.92,y:y+0.16,w:2.55,h:0.6,fontSize:29,bold:true,color:i===0?ACC_L:WHT,fontFace:H,isTextBox:true,margin:0});
  s.addText(l,{x:9.92,y:y+0.79,w:2.55,h:0.36,fontSize:10,color:"8B9BA6",fontFace:B,isTextBox:true,margin:0});
});
s.addNotes("면적 항은 USGS 값이 확률이 아니라 격자 칸당 피복 비율이라는 점을 보정한다. LOEO는 정답을 학습에 쓰면서도 성능을 정직하게 재는 절차다.");

/* ── 2 한 장 요약 ── */
s=pres.addSlide(); s.background={color:WHT};
title(s,"한 장 요약","60회 실행 결과를 네 문장으로");
[["제안은 A 계열에서 깨끗하게 작동했다","LS 0.7222 → 0.8039. 짝지은 부트스트랩 P(개선>0) = 0.981, 5회차 κ가 전부 양수(+0.93~+1.37)로 안정적이었다.",ACC],
 ["면적 항 위에서는 이득이 없다","B2 0.8507 ≤ B0 0.8550. 면적 항이 산지 정보를 이미 담고 있어(corr 0.53) 배울 것이 남아 있지 않았다.",NEG],
 ["성능은 사전확률이 거의 다 만든다","사전 log(π̄)+log k 만으로 0.8400. 음성이 충분한 세 지진에서는 사전과 사후가 완전히 같다(둘 다 0.8177).",ACC],
 ["적용은 가장 적게 학습하는 쪽","B0 — 사전 학습 파라미터 0개, 산사태 정답 미사용, LS 0.8550. LQ까지 챙기려면 C0(+b_LQ 하나).",POS]]
 .forEach(([t,d,c],i)=>{
  const y=1.62+i*1.22;
  card(s,0.65,y,12.0,1.06);
  num(s,0.9,y+0.18,i+1,c);
  s.addText(t,{x:1.48,y:y+0.1,w:10.9,h:0.34,fontSize:15,bold:true,color:INK,fontFace:H,isTextBox:true,margin:0});
  s.addText(d,{x:1.48,y:y+0.46,w:10.9,h:0.52,fontSize:11.5,color:MUT,lineSpacing:15,fontFace:B,isTextBox:true,margin:0});
});
s.addText("참고 기준값 — USGS prior 단독 0.797 · 산지 비율 단독 0.806 · 면적 항 prior 단독 0.840 · 면적 항 사후(26.09.16 자료) 0.855",
  {x:0.65,y:6.62,w:12.0,h:0.34,fontSize:10.5,color:MUT,italic:true,fontFace:B,isTextBox:true,margin:0});
s.addNotes("0.8550은 새로 얻은 값이 아니다. 기존 자료의 0.855와 소수 넷째 자리까지 같다. 새로 밝혀진 것은 왜 그것을 넘지 못하는가다.");

/* ── 3 배경 ── */
s=pres.addSlide(); s.background={color:WHT};
title(s,"왜 이 실험을 했는가","지금 모델은 피해 건수(NLL)만 보고 학습하고, 산사태 정답은 평가에만 쓴다");
[["산지 비율은 그 자체로 잘 맞힌다","단독 LS 가중 AUC 0.806",POS],
 ["그런데 회귀식에 넣으면 떨어진다","LS AUC 0.651로 하락",NEG],
 ["prior에 κ·m으로 넣어도 안 배운다","κ = 0.05, 사실상 0",NEG]].forEach(([t,d,c],i)=>{
  const x=0.65+i*4.05; card(s,x,1.62,3.75,1.5);
  s.addShape(pres.ShapeType.ellipse,{x:x+0.28,y:1.86,w:0.28,h:0.28,fill:{color:c},line:{color:c,width:0}});
  s.addText(t,{x:x+0.28,y:2.26,w:3.2,h:0.52,fontSize:12.5,bold:true,color:INK,lineSpacing:16,fontFace:H,isTextBox:true,margin:0});
  s.addText(d,{x:x+0.28,y:2.76,w:3.2,h:0.3,fontSize:11,color:MUT,fontFace:B,isTextBox:true,margin:0});
});
s.addShape(pres.ShapeType.roundRect,{x:0.65,y:3.36,w:12.0,h:1.02,rectRadius:0.08,fill:{color:DARK},line:{color:DARK,width:0}});
s.addText("교수님 제안",{x:0.95,y:3.52,w:2.2,h:0.3,fontSize:11.5,bold:true,color:ACC_L,fontFace:B,isTextBox:true,margin:0});
s.addText("산사태 정답을 학습에도 쓰되, 공정하게 평가하려고 지진을 하나씩 가려서 시험한다.",
  {x:0.95,y:3.84,w:11.4,h:0.4,fontSize:15,color:WHT,fontFace:H,isTextBox:true,margin:0});
s.addText("이 제안을 두 가지 사전확률 위에서 실행했다",{x:0.65,y:4.6,w:12.0,h:0.32,fontSize:12.5,bold:true,color:INK,fontFace:B,isTextBox:true,margin:0});
tbl(s,[[hl("계열"),hl("LS 사전확률 z_LS"),hl("LQ 사전확률 z_LQ"),hl("학습 파라미터")],
 ["A (기존)","a·logit(π̄_LS) + b_LS  ( + κ·m )","a·logit(π̄_LQ) + b_LQ","a, b, κ"],
 ["B (면적 항)","log(π̄_LS) + log k_LS + b_LS  ( + κ·m )","log(π̄_LQ) + log k_LQ + b_LQ","b, κ"]],
 {x:0.65,y:4.98,w:12.0,colW:[1.6,4.75,3.65,2.0],rowH:0.36,fontSize:11});
s.addText("π̄ = LS_prior(평균)·LQ_prior(평균)   ·   k = area_km2 ÷ 격자 칸 넓이 (LS 7.5″, LQ 15″)   ·   m = 학습 418행 기준 표준화한 mountain_ratio",
  {x:0.65,y:6.24,w:12.0,h:0.32,fontSize:10.5,color:MUT,italic:true,fontFace:B,isTextBox:true,margin:0});
s.addNotes("면적 항은 USGS 값이 칸당 피복 비율이라는 점에서 유도된다. 칸이 독립이면 기대 칸 수 λ = π̄ × k 이고, log λ = log π̄ + log k 다.");

/* ── 4 LOEO 설계 ── */
s=pres.addSlide(); s.background={color:WHT};
title(s,"LOEO — 지진 하나씩 가리기","정답을 학습에 쓰면서도 성능을 정직하게 재는 방법");
[["시험 지진 1개 선택","5개 지진을 돌아가며"],["그 지진의 ls_flag만 가림","피해 건수는 NLL에 그대로"],
 ["나머지로 BCE 학습","loss = 기존 loss + ω × Σ BCE"],["가린 지진으로만 채점","정답을 안 본 예측으로 AUC"]]
 .forEach(([t,d],i)=>{
  const x=0.65+i*3.08; card(s,x,1.6,2.82,1.68);
  num(s,x+0.24,1.8,i+1);
  s.addText(t,{x:x+0.24,y:2.3,w:2.34,h:0.5,fontSize:12,bold:true,color:INK,lineSpacing:15,fontFace:H,isTextBox:true,margin:0});
  s.addText(d,{x:x+0.24,y:2.78,w:2.36,h:0.44,fontSize:10.5,color:MUT,lineSpacing:13,fontFace:B,isTextBox:true,margin:0});
  if(i<3) s.addText("›",{x:x+2.62,y:2.22,w:0.3,h:0.4,fontSize:24,bold:true,color:ACC,align:"center",fontFace:H,isTextBox:true,margin:0});
});
s.addText("5회차 구성",{x:0.65,y:3.44,w:6,h:0.3,fontSize:12.5,bold:true,color:INK,fontFace:B,isTextBox:true,margin:0});
tbl(s,[[hd("회차"),hd("시험 지진"),hd("시험 행"),hd("양성/음성"),hd("BCE 대상")],
 ["1","2000 돗토리","24","15 / 9","101"],["2","2004 니가타현주에쓰","10","8 / 2","115"],
 ["3","2016 구마모토","29","26 / 3","96"],["4","2018 오사카","7","5 / 2","118"],
 ["5","2018 훗카이도","13","9 / 4","112"]],
 {x:0.65,y:3.8,w:6.5,colW:[0.7,2.5,1.0,1.2,1.1],rowH:0.315,fontSize:10.5,align:"center"});
s.addText("결과를 보기 전에 고정한 값",{x:7.5,y:3.44,w:5.15,h:0.3,fontSize:12.5,bold:true,color:INK,fontFace:B,isTextBox:true,margin:0});
tbl(s,[[hl("항목"),hl("값")],["ω (주 조건)","4.35  ( = 418 ÷ 96 )"],["ω (대조군 / 민감도)","0 / 1 / 10"],
 ["산지 변수","국세조사 mountain_ratio"],["BCE 확률","사전 q_LS (사후 아님)"],
 ["공변량","목조만 (산지 η는 회귀식에 없음)"],["공통","3000 epoch · lr 0.02 · λγ 10 · seed 0"]],
 {x:7.5,y:3.8,w:5.15,colW:[1.9,3.25,],rowH:0.315,fontSize:10.5});
s.addText("음성이 0인 4개 지진(2007·2008·2021·2024)은 AUC가 정의되지 않아 채점에서 빠지지만 BCE 대상에는 매 회차 포함한다. 가중평균은 24·10·29·7·13 ÷ 83.",
  {x:0.65,y:6.22,w:12.0,h:0.34,fontSize:10.5,color:MUT,italic:true,fontFace:B,isTextBox:true,margin:0});
s.addNotes("시험 지진의 피해 건수는 NLL에 그대로 들어간다. 가리는 것은 그 지진의 ls_flag뿐이다.");

/* ── 5 사전등록 vs 사후 탐색 ── */
s=pres.addSlide(); s.background={color:WHT};
title(s,"사전등록과 사후 탐색","같은 표에 섞으면 안 되는 두 종류의 실험이 있다");
card(s,0.65,1.62,5.9,3.1,"E8F0F4",ACC);
s.addText("판정 대상",{x:0.95,y:1.8,w:5.3,h:0.28,fontSize:10.5,bold:true,color:ACC,charSpacing:1,fontFace:B,isTextBox:true,margin:0});
s.addText("사전등록 — A · B 계열 30회",{x:0.95,y:2.1,w:5.3,h:0.36,fontSize:16,bold:true,color:INK,fontFace:H,isTextBox:true,margin:0});
s.addText("지시서 §3(고정값)과 §4(조건표)는 결과를 보기 전에 못박은 것이다. ω = 4.35, 라벨 기준, 산지 변수, 성공 조건까지 미리 정했다.\n\n성공·실패 판정은 이 조건들로만 한다. §0이 “결과를 본 뒤에 바꾸지 않는다”고 정해 두었다.",
  {x:0.95,y:2.54,w:5.3,h:2.0,fontSize:11.5,color:MUT,lineSpacing:16,fontFace:B,isTextBox:true,margin:0});
card(s,6.75,1.62,5.9,3.1,SURF,LINE);
s.addText("판정 대상 아님",{x:7.05,y:1.8,w:5.3,h:0.28,fontSize:10.5,bold:true,color:MUT,charSpacing:1,fontFace:B,isTextBox:true,margin:0});
s.addText("사후 탐색 — C 계열 · 중심화 30회",{x:7.05,y:2.1,w:5.3,h:0.36,fontSize:16,bold:true,color:INK,fontFace:H,isTextBox:true,margin:0});
s.addText("결과를 본 뒤에 떠오른 아이디어다. 그대로 판정표에 넣으면 “좋아 보이는 것을 골랐다”가 되므로 별도 폴더·별도 엑셀로 분리했다.",
  {x:7.05,y:2.54,w:5.3,h:0.72,fontSize:11.5,color:MUT,lineSpacing:16,fontFace:B,isTextBox:true,margin:0});
s.addText([{text:"b_LQ 고정 해제",options:{bold:true,breakLine:false}},
           {text:"  — LQ 확률 수준이 어긋난 것을 보고 (C0 · C2, 6회)",options:{breakLine:true}},
           {text:"log k 중심화",options:{bold:true,breakLine:false}},
           {text:"  — b 상자가 걸리는 것을 보고 (24회)",options:{breakLine:false}}],
  {x:7.05,y:3.34,w:5.3,h:0.9,fontSize:11.5,color:MUT,lineSpacing:17,fontFace:B,isTextBox:true,margin:0});
s.addShape(pres.ShapeType.roundRect,{x:0.65,y:4.94,w:12.0,h:1.5,rectRadius:0.08,fill:{color:DARK},line:{color:DARK,width:0}});
s.addText("왜 나누는가",{x:0.95,y:5.12,w:2.5,h:0.3,fontSize:11.5,bold:true,color:ACC_L,fontFace:B,isTextBox:true,margin:0});
s.addText("사전등록 조건만으로 판정하면 “미리 세운 가설이 맞았는가”를 답할 수 있다. 결과를 보고 조건을 추가하면 그 답이 “여러 개 중 좋은 것을 골랐다”로 바뀌어 의미를 잃는다.",
  {x:0.95,y:5.44,w:11.4,h:0.38,fontSize:12,color:"C3CFD6",fontFace:B,isTextBox:true,margin:0});
s.addText("그래서 사후 탐색 결과는 “다음 실험 제안”으로만 쓴다. 정식 결과로 올리려면 조건을 미리 고정한 새 지시서로 다시 돌려야 한다.",
  {x:0.95,y:5.88,w:11.4,h:0.38,fontSize:12,bold:true,color:WHT,fontFace:B,isTextBox:true,margin:0});
s.addNotes("이 구분이 이번 보고의 신뢰도를 지탱한다. B0이 1위라는 것도, A2가 성공이라는 것도 모두 사전등록 조건 안에서 나온 결론이다.");

/* ── 6 표 A 설정 ── */
s=pres.addSlide(); s.background={color:WHT};
title(s,"표 A — 조건별로 무엇을 어떻게 설정했나","회귀·우도 쪽(피해 건수 6채널, 음이항, 목조 공변량, λγ=10)은 모든 조건에서 동일하다. 바뀌는 것은 사전확률 식뿐이다");
tbl(s,[[hd("ID"),hd("링크"),hd("b_LS"),hd("b_LQ"),hd("κ·m"),hd("log k 평균 빼기"),hd("ω"),hd("실행")],
 ["A0","logit(π̄)  면적 항 없음","학습 [−2, 2]","학습 [−2, 2]",g("없음"),g("해당 없음"),g("0"),"1"],
 ["A1","logit(π̄)  면적 항 없음","학습 [−2, 2]","학습 [−2, 2]","학습",g("해당 없음"),g("0"),"1"],
 [bd("A2"),"logit(π̄)  면적 항 없음","학습 [−2, 2]","학습 [−2, 2]","학습",g("해당 없음"),bd("4.35"),bd("5")],
 [bd("B0",ACC),bd("log(π̄) + log k",ACC),bd("0 고정",ACC),bd("0 고정",ACC),g("없음"),bd("안 뺌 (b 고정)",NEG),g("0"),"1"],
 ["B1","log(π̄) + log k","학습 [−2, 4]","0 고정","학습",{text:"안 뺌",options:{color:NEG}},g("0"),"1"],
 [bd("B2"),"log(π̄) + log k","학습 [−2, 4]","0 고정","학습",{text:"안 뺌",options:{color:NEG}},bd("4.35"),bd("5")],
 ["B2-ω1","log(π̄) + log k","학습 [−2, 4]","0 고정","학습",{text:"안 뺌",options:{color:NEG}},"1","5"],
 ["B2-ω10","log(π̄) + log k","학습 [−2, 4]","0 고정","학습",{text:"안 뺌",options:{color:NEG}},"10","5"],
 ["B0-logit",bd("logit(π̄) + log k"),"0 고정","0 고정",g("없음"),{text:"안 뺌",options:{color:NEG}},g("0"),"1"],
 ["B2-logit",bd("logit(π̄) + log k"),"학습 [−2, 4]","0 고정","학습",{text:"안 뺌",options:{color:NEG}},"4.35","5"],
 [g("C0"),"log(π̄) + log k","0 고정",bd("학습 [−10, 4]",POS),g("없음"),{text:"안 뺌",options:{color:NEG}},g("0"),"1"],
 [g("C2"),"log(π̄) + log k","학습 [−2, 4]",bd("학습 [−10, 4]",POS),"학습",{text:"안 뺌",options:{color:NEG}},"4.35","5"]],
 {x:0.65,y:1.62,w:12.0,colW:[1.1,2.55,1.55,1.55,0.95,2.0,0.8,0.7],rowH:0.335,fontSize:9.5,align:"center"});
s.addText("a는 A 계열에서만 학습하고 범위는 [0.5, 2] · 초기값 1. B·C 계열은 a = c = 1로 고정. κ는 스칼라 하나 · 초기값 0 · 범위 제약 없음 · LS에만 들어간다. b는 전부 sigmoid 재매개변수화로 범위를 지키고 초기값은 0. ω = 0이면 BCE 항이 loss에 전혀 들어가지 않는다.",
  {x:0.65,y:5.78,w:12.0,h:0.6,fontSize:10.5,color:MUT,lineSpacing:14,fontFace:B,isTextBox:true,margin:0});
s.addText("C0 · C2는 사후 탐색이다. 판정표에는 들어가지 않는다.",
  {x:0.65,y:6.44,w:12.0,h:0.3,fontSize:10.5,color:MUT,italic:true,fontFace:B,isTextBox:true,margin:0});
s.addNotes("표 A의 'log k 평균 빼기' 열이 전부 '안 뺌'인 것이 중요하다. 사전등록 30회는 센터링을 하지 않았고, 센터링은 별도 사후 탐색에서만 켰다.");

/* ── 7 표 B 학습 결과 ── */
s=pres.addSlide(); s.background={color:WHT};
title(s,"표 B — 무엇이 학습되어 나왔나","5회차 조건은 회차별 최솟값 ~ 최댓값");
tbl(s,[[hd("ID"),hd("a_LS"),hd("b_LS"),hd("b_LQ"),hd("κ"),hd("파라미터"),hl("읽는 법")],
 ["A0","+0.5040","+1.9894",g("—"),g("없음"),"48","a는 하한 0.5, b는 상한 2에 붙었다. 상자가 걸린다."],
 ["A1","+0.5041","+1.9895",g("—"),"+0.2795","49","감독 없이도 κ가 양수로 갔다. 다만 작다."],
 [bd("A2"),"+0.5010 ~ +0.5012","+1.9953 ~ +1.9960",g("—"),bd("+0.9259 ~ +1.3698",POS),"49",
  {text:"κ 5회차 전부 양수. 감독이 κ를 세 배 이상 키웠다.",options:{bold:true}}],
 [bd("B0",ACC),g("1 고정"),bd("0 고정",ACC),bd("0 고정",ACC),g("없음"),bd("44",ACC),
  {text:"사전에 학습 파라미터가 하나도 없다.",options:{bold:true,color:ACC}}],
 ["B1",g("1 고정"),bd("−1.9754",NEG),"0 고정",bd("−0.8095",NEG),"46","b가 하한 −2에 붙고 κ가 크게 음수로 갔다. 사전이 망가진다."],
 [bd("B2"),g("1 고정"),"−0.5571 ~ −0.0022","0 고정",bd("−0.4070 ~ +0.1583",NEG),"46",
  {text:"κ 부호가 회차마다 뒤집힌다. 훗카이도 회차만 양수.",options:{bold:true}}],
 ["B2-ω1",g("1 고정"),"−1.1132 ~ −0.7023","0 고정","−0.4777 ~ −0.1344","46","ω가 작으면 κ가 전부 음수다."],
 ["B2-ω10",g("1 고정"),"−0.4631 ~ +0.0944","0 고정","−0.4226 ~ +0.1692","46","ω = 4.35과 사실상 같다. BCE가 포화됐다."],
 [g("C0"),g("1 고정"),"0 고정",bd("−4.1165",POS),g("없음"),"45","q_LQ 중앙값을 0.9145 → 0.1485로 끌어내렸다."],
 [g("C2"),g("1 고정"),"−0.5123 ~ +0.0489","−4.1258 ~ −4.0976","−0.3849 ~ +0.1932","47","b_LQ는 회차와 무관하게 −4.1 근처로 수렴한다."]],
 {x:0.65,y:1.58,w:12.0,colW:[1.0,1.35,1.75,1.5,1.75,0.85,3.8],rowH:0.415,fontSize:9.5,align:"center"});
s.addText("A 계열 세 조건 전부 a와 b가 범위 경계에 붙어 있다(a 0.504는 하한 0.5, b 1.99는 상한 2). B1의 b_LS도 하한 −2에 붙었다. 상자가 실제로 걸리고 있다는 뜻이다.",
  {x:0.65,y:6.3,w:12.0,h:0.34,fontSize:10.5,color:MUT,italic:true,fontFace:B,isTextBox:true,margin:0});
s.addNotes("표 B에서 A2의 κ가 전부 양수이고 B2는 뒤집힌다는 것이 판정 결과를 직접 설명한다.");

/* ── 8 LS 결과 ── */
s=pres.addSlide(); s.background={color:WHT};
title(s,"결과 ① 산사태(LS)","가린 지진으로만 채점한 사후 가중 AUC. 위로 갈수록 좋다");
s.addChart(pres.ChartType.bar,[{name:"LS 사후 가중 AUC",
  labels:["A0  기존 사전","A1  + κ·m","B1  면적 항 + κ·m","A2  제안 (A 계열)","B2-ω1","B2  제안 + 면적 항","B0  면적 항만"],
  values:[0.7222,0.7479,0.7285,0.8039,0.8136,0.8507,0.8550]}],
  {x:0.65,y:1.6,w:7.7,h:4.55,barDir:"bar",barGapWidthPct:45,chartColors:[ACC],
   showTitle:false,showLegend:false,valAxisMinVal:0.65,valAxisMaxVal:0.90,valAxisMajorUnit:0.05,
   catAxisLabelColor:MUT,valAxisLabelColor:MUT,catAxisLabelFontSize:11,valAxisLabelFontSize:10,
   catAxisLabelFontFace:B,valAxisLabelFontFace:B,valGridLine:{color:"E7ECEF",size:1},
   catGridLine:{style:"none"},showValue:true,dataLabelFontSize:11,dataLabelFontFace:B,
   dataLabelColor:INK,dataLabelPosition:"outEnd",dataLabelFormatCode:"0.0000"});
card(s,8.65,1.6,4.0,4.55);
s.addText("읽는 법",{x:8.95,y:1.8,w:3.45,h:0.3,fontSize:12.5,bold:true,color:INK,fontFace:H,isTextBox:true,margin:0});
[["A2가 A0을 크게 넘었다","0.7222 → 0.8039  (+0.0817)",POS],
 ["B2는 B0을 넘지 못했다","0.8550 → 0.8507  (−0.0044)",NEG],
 ["1등은 학습을 안 한 B0","사전 학습 파라미터 0개",ACC],
 ["B1이 최하위권","면적 항이 있어도 κ를 감독 없이 학습시키면 0.7285로 망가진다",NEG]]
 .forEach(([t,d,c],i)=>{
  const y=2.24+i*0.98;
  s.addShape(pres.ShapeType.ellipse,{x:8.95,y:y+0.05,w:0.19,h:0.19,fill:{color:c},line:{color:c,width:0}});
  s.addText(t,{x:9.28,y:y-0.02,w:3.1,h:0.28,fontSize:11.5,bold:true,color:INK,fontFace:B,isTextBox:true,margin:0});
  s.addText(d,{x:9.28,y:y+0.26,w:3.1,h:0.56,fontSize:10.5,color:MUT,lineSpacing:13,fontFace:B,isTextBox:true,margin:0});
});
s.addText("LS 평가 125행 중 AUC가 정의되는 5개 지진 83행. 음성은 20개뿐이라 구간이 넓다.",
  {x:0.65,y:6.34,w:12.0,h:0.32,fontSize:10.5,color:MUT,italic:true,fontFace:B,isTextBox:true,margin:0});
s.addNotes("B0은 산사태 정답을 한 번도 쓰지 않았고 사전에 학습 파라미터가 없는데도 1위다.");

/* ── 9 판정 ── */
s=pres.addSlide(); s.background={color:WHT};
title(s,"판정","성공 조건도 결과를 보기 전에 고정했다 — 기준선 초과 + P(차이>0) ≥ 95% + κ 부호 일치");
card(s,0.65,1.6,5.9,2.3,"E8F1EC",POS);
s.addText("A2   성공",{x:0.95,y:1.78,w:3.0,h:0.44,fontSize:22,bold:true,color:POS,fontFace:H,isTextBox:true,margin:0});
s.addText("교수님 제안 · A 계열",{x:0.95,y:2.24,w:5.3,h:0.28,fontSize:11,color:MUT,fontFace:B,isTextBox:true,margin:0});
[["가중 AUC","0.8039  >  A0 0.7222"],["P(차이 > 0)","0.9813  ≥  0.95"],["κ 부호","5회차 전부 양수 (+0.93 ~ +1.37)"]].forEach(([k,v],i)=>{
  s.addText(k,{x:0.95,y:2.62+i*0.38,w:1.5,h:0.3,fontSize:11,color:MUT,fontFace:B,isTextBox:true,margin:0});
  s.addText(v,{x:2.5,y:2.62+i*0.38,w:3.8,h:0.3,fontSize:11.5,bold:true,color:INK,fontFace:B,isTextBox:true,margin:0});
});
card(s,6.75,1.6,5.9,2.3,"F7EAE6",NEG);
s.addText("B2   실패",{x:7.05,y:1.78,w:3.0,h:0.44,fontSize:22,bold:true,color:NEG,fontFace:H,isTextBox:true,margin:0});
s.addText("제안 + 면적 항 · B 계열",{x:7.05,y:2.24,w:5.3,h:0.28,fontSize:11,color:MUT,fontFace:B,isTextBox:true,margin:0});
[["가중 AUC","0.8507  ≤  B0 0.8550"],["P(차이 > 0)","0.0000"],["κ 부호","4회 음수 / 1회 양수 — 뒤집힘"]].forEach(([k,v],i)=>{
  s.addText(k,{x:7.05,y:2.62+i*0.38,w:1.5,h:0.3,fontSize:11,color:MUT,fontFace:B,isTextBox:true,margin:0});
  s.addText(v,{x:8.6,y:2.62+i*0.38,w:3.8,h:0.3,fontSize:11.5,bold:true,color:INK,fontFace:B,isTextBox:true,margin:0});
});
s.addText("짝지은 부트스트랩 3,000회 (seed 0) — 지진 안에서 양성·음성을 따로 복원추출, 모든 조건이 같은 표본",
  {x:0.65,y:4.12,w:12.0,h:0.3,fontSize:12,bold:true,color:INK,fontFace:B,isTextBox:true,margin:0});
tbl(s,[[hd("비교"),hd("차이 (관측)"),hd("95% 구간"),hd("P(차이 > 0)"),hl("해석")],
 [bd("A2 − A0"),"+0.0817","[+0.0031, +0.1644]",bd("0.9813",POS),"제안이 기존 사전을 유의하게 개선"],
 ["A2 − A1","+0.0560","[+0.0004, +0.1246]",{text:"0.9763",options:{color:POS}},"정답을 쓴 쪽이 안 쓴 쪽보다 낫다"],
 [bd("B2 − B0"),"−0.0044","[−0.0261, 0.0000]",bd("0.0000",NEG),"재표본 3,000벌 전부에서 못 넘음"],
 ["B2 − B1","+0.1222","[+0.0514, +0.1981]",{text:"1.0000",options:{color:POS}},"감독이 있으면 κ 폭주는 막힌다"],
 ["B2 − A2","+0.0468","[−0.0287, +0.1322]","0.8860","면적 항이 앞서지만 구간은 0을 걸침"],
 [{text:"C0 − B0 (LQ)",options:{color:MUT}},"+0.0342","[+0.0009, +0.0698]",{text:"0.9780",options:{color:POS}},
  {text:"사후 탐색 — b_LQ 해제가 LQ를 개선",options:{color:MUT}}]],
 {x:0.65,y:4.5,w:12.0,colW:[1.65,1.5,2.2,1.4,5.25],rowH:0.325,fontSize:10.5,align:"center"});
s.addNotes("B2−B1이 P=1.0인 것이 중요하다. 감독을 붙이면 κ 폭주는 막아준다. 다만 그래봐야 아무것도 안 넣은 B0을 못 넘는다.");

/* ── 10 성능은 사전이 다 만든다 ── */
s=pres.addSlide(); s.background={color:WHT};
title(s,"성능은 사전확률이 거의 다 만든다","왼쪽은 회귀를 거치지 않은 사전 점수, 오른쪽은 그 사전이 회귀·우도를 지나며 얼마나 나아지는지");
s.addChart(pres.ChartType.bar,[
 {name:"LS",labels:["USGS π̄ 단독","시정촌 면적 log k 단독","산지 비율 단독","π̄ + 면적 항"],values:[0.7969,0.8214,0.8060,0.8400]},
 {name:"LQ",labels:["USGS π̄ 단독","시정촌 면적 log k 단독","산지 비율 단독","π̄ + 면적 항"],values:[0.7154,0.5470,0.4287,0.7698]}],
 {x:0.65,y:1.6,w:6.4,h:3.4,barDir:"col",barGapWidthPct:55,chartColors:[ACC,POS_L],
  showTitle:false,showLegend:true,legendPos:"t",legendColor:MUT,legendFontSize:10.5,
  catAxisLabelColor:MUT,valAxisLabelColor:MUT,catAxisLabelFontSize:9.5,valAxisLabelFontSize:10,
  catAxisLabelFontFace:B,valAxisLabelFontFace:B,valGridLine:{color:"E7ECEF",size:1},
  catGridLine:{style:"none"},valAxisMinVal:0.35,valAxisMaxVal:0.90,valAxisMajorUnit:0.1,
  showValue:true,dataLabelFontSize:9,dataLabelFontFace:B,dataLabelColor:INK,
  dataLabelPosition:"outEnd",dataLabelFormatCode:"0.0000"});
s.addText("LQ에서는 면적 단독이 0.5470으로 우연 수준인데도 π̄와 더하면 0.7154 → 0.7698로 오른다. 면적이 라벨을 직접 켜는 게 아니라 λ = π̄ × k 가 작동한다는 뜻이다.",
  {x:0.65,y:5.06,w:6.4,h:0.6,fontSize:10.5,color:MUT,lineSpacing:14,fontFace:B,isTextBox:true,margin:0});
s.addText("LS 사전 → 사후 (가중 AUC)",{x:7.25,y:1.6,w:5.4,h:0.3,fontSize:12,bold:true,color:INK,fontFace:B,isTextBox:true,margin:0});
tbl(s,[[hd("ID"),hd("사전 (83)"),hd("사후 (83)"),hd("사전 (66)"),hd("사후 (66)")],
 ["A0","0.7969",bd("0.7222",NEG),"0.7635",{text:"0.7286",options:{color:NEG}}],
 ["A1","0.7986",{text:"0.7479",options:{color:NEG}},"0.7562","0.7704"],
 ["A2","0.8341",{text:"0.8039",options:{color:NEG}},"0.8103","0.8018"],
 [bd("B0",ACC),bd("0.8400",ACC),bd("0.8550",ACC),bd("0.8177",ACC),bd("0.8177",ACC)],
 ["B1","0.7660",{text:"0.7285",options:{color:NEG}},"0.7554","0.7449"],
 ["B2","0.8220",{text:"0.8507",options:{color:POS}},"0.7951","0.8122"]],
 {x:7.25,y:1.98,w:5.4,colW:[0.8,1.18,1.18,1.12,1.12],rowH:0.335,fontSize:10.5,align:"center"});
s.addText("83 = AUC가 정의되는 5개 지진 전부.   66 = 그중 음성이 3개 이상인 세 개(돗토리 9 · 구마모토 3 · 훗카이도 4).",
  {x:7.25,y:4.36,w:5.4,h:0.5,fontSize:10,color:MUT,lineSpacing:13,fontFace:B,isTextBox:true,margin:0});
s.addShape(pres.ShapeType.roundRect,{x:7.25,y:4.92,w:5.4,h:0.74,rectRadius:0.08,fill:{color:DARK},line:{color:DARK,width:0}});
s.addText("B0은 음성이 충분한 세 지진에서 사전 = 사후다. 차이 0.0000.",
  {x:7.5,y:5.06,w:4.95,h:0.46,fontSize:11.5,bold:true,color:WHT,lineSpacing:15,fontFace:B,isTextBox:true,margin:0});
s.addText("전체 83행에서 보이는 +0.015는 전부 2004 니가타(양성 8 / 음성 2 = 16쌍)에서 0.8750 → 1.0000으로 나온 것이고, 나머지 네 지진은 사전·사후 AUC가 한 자리도 다르지 않다.   즉 지금 산사태 순위 성능은 엑셀 두 열(LS_prior(평균), area_km2)이 거의 다 만들고 있다.",
  {x:0.65,y:5.82,w:12.0,h:0.72,fontSize:11,color:INK,lineSpacing:15,fontFace:B,isTextBox:true,margin:0});
s.addNotes("회귀 44개 파라미터와 음이항 우도가 LS 순위에 보태는 것이 거의 없다. A 계열에서는 오히려 깎는다.");

/* ── 11 Δ 읽는 법 ── */
s=pres.addSlide(); s.background={color:WHT};
title(s,"사전 → 사후 차이(Δ)를 어떻게 읽나","Δ가 큰 쪽이 좋은 조건은 아니다. 그런데 무의미한 지표도 아니다");
card(s,0.65,1.6,12.0,1.16);
s.addText("B2의 Δ는 +0.0286으로 B0의 +0.0151보다 크다. 그래도 B2가 더 좋은 조건은 아니다 — B2는 자기 사전을 먼저 망가뜨렸다.",
  {x:0.95,y:1.76,w:11.4,h:0.36,fontSize:13,bold:true,color:INK,fontFace:H,isTextBox:true,margin:0});
s.addText("κ = −0.41이 사전을 0.8400에서 0.8220으로 끌어내렸고, 우도가 +0.0286을 회복했지만 최종은 0.8507로 여전히 B0의 0.8550 아래다.\n시험 점수로 치면 60 → 80점(+20)과 85 → 90점(+5)이고, 우리가 쓸 모델은 최종 예측 성능으로 고른다.",
  {x:0.95,y:2.14,w:11.4,h:0.56,fontSize:11.5,color:MUT,lineSpacing:15,fontFace:B,isTextBox:true,margin:0});
s.addText("Δ가 커지는 이유는 둘인데, 사전 순위가 그대로인지로 갈린다",
  {x:0.65,y:2.94,w:12.0,h:0.32,fontSize:12.5,bold:true,color:INK,fontFace:B,isTextBox:true,margin:0});
tbl(s,[[hd("비교"),hl("사전 순위"),hd("Δ"),hl("해석")],
 [bd("B2 vs B0  (LS)"),{text:"나빠짐   0.8400 → 0.8220",options:{color:NEG,bold:true}},"+0.0286",
  {text:"사전이 약해져 우도가 메울 여지가 생긴 것 — 나쁜 Δ",options:{color:NEG}}],
 [bd("C0 vs B0  (LQ)"),{text:"완전히 같음   0.7698 = 0.7698",options:{color:POS,bold:true}},bd("+0.0460",POS),
  {text:"순위는 그대로인데 확률 수준이 맞아 우도가 제대로 작동 — 좋은 Δ",options:{color:POS}}]],
 {x:0.65,y:3.32,w:12.0,colW:[2.3,3.5,1.2,5.0],rowH:0.52,fontSize:11,align:"center"});
s.addShape(pres.ShapeType.roundRect,{x:0.65,y:4.68,w:12.0,h:1.28,rectRadius:0.08,fill:{color:DARK},line:{color:DARK,width:0}});
s.addText("C0이 좋은 Δ의 교과서 사례다",{x:0.95,y:4.86,w:11.4,h:0.32,fontSize:13,bold:true,color:ACC_L,fontFace:H,isTextBox:true,margin:0});
s.addText("사전 순위가 B0과 소수 넷째 자리까지 같은데 Δ가 네 배(+0.0460 vs +0.0114)이고, 최종값도 LQ 1위다.\nb_LQ가 순위를 건드리지 않고 확률 수준만 옮겼기 때문에 4상태 가중치가 제대로 잡힌 결과다.",
  {x:0.95,y:5.2,w:11.4,h:0.62,fontSize:11.5,color:"C3CFD6",lineSpacing:16,fontFace:B,isTextBox:true,margin:0});
s.addText("정리 — 조건을 고르는 기준은 최종 사후 AUC다. Δ는 모델 기계가 일을 하는지 보는 진단 지표이고, 사전 순위와 함께 읽어야 뜻이 생긴다.",
  {x:0.65,y:6.14,w:12.0,h:0.34,fontSize:11.5,bold:true,color:INK,fontFace:B,isTextBox:true,margin:0});
s.addNotes("이 슬라이드는 'prior보다 높으면 좋은 것 아닌가'라는 질문에 답한다. 최종값이 기준이고, Δ는 사전 순위와 함께 봐야 한다.");

/* ── 12 왜 실패했나 ── */
s=pres.addSlide(); s.background={color:WHT};
title(s,"B2는 왜 실패했나","κ가 순위가 아니라 확률 수준을 고치는 데 쓰였다");
s.addText("회차별 κ",{x:0.65,y:1.58,w:5.3,h:0.3,fontSize:12.5,bold:true,color:INK,fontFace:B,isTextBox:true,margin:0});
tbl(s,[[hd("시험 지진"),hd("A2  κ"),hd("B2  κ")],
 ["2000 돗토리",{text:"+0.9356",options:{color:POS}},{text:"−0.0254",options:{color:NEG}}],
 ["2004 니가타현주에쓰",{text:"+0.9259",options:{color:POS}},{text:"−0.1898",options:{color:NEG}}],
 ["2016 구마모토",{text:"+1.3698",options:{color:POS}},{text:"−0.4070",options:{color:NEG}}],
 ["2018 오사카",{text:"+1.0417",options:{color:POS}},{text:"−0.2655",options:{color:NEG}}],
 ["2018 훗카이도",{text:"+0.9871",options:{color:POS}},bd("+0.1583","C98B3A")]],
 {x:0.65,y:1.94,w:5.3,colW:[2.7,1.3,1.3],rowH:0.355,fontSize:11,align:"center"});
s.addText("강제로 κ = +1을 넣으면 사전이 0.8400 → 0.8539로 오른다. 학습된 κ(−0.41)는 순위를 최대화하는 방향의 반대로 갔다.",
  {x:0.65,y:4.14,w:5.3,h:0.7,fontSize:11,color:NEG,lineSpacing:15,fontFace:B,isTextBox:true,margin:0});
s.addText("2018 훗카이도 — 산이 많은 곳이 오히려 음성이다",{x:6.25,y:1.58,w:6.4,h:0.3,fontSize:12.5,bold:true,color:INK,fontFace:B,isTextBox:true,margin:0});
tbl(s,[[hd("시정촌"),hd("산사태"),hd("산지 z"),hd("q 변화 (B0→B2)")],
 [bd("히다카초 (日高町)"),bd("없음",NEG),"+0.99","0.9706 → 0.9730"],
 [bd("유바리시 (夕張市)"),bd("없음",NEG),"+1.35","0.9612 → 0.9663"],
 ["기타히로시마시 (北広島市)",{text:"있음",options:{color:POS}},"−0.57","0.6641 → 0.6290"],
 ["유니초 (由仁町)",{text:"있음",options:{color:POS}},"−0.63","0.8282 → 0.8039"]],
 {x:6.25,y:1.94,w:6.4,colW:[2.5,0.95,1.05,1.9],rowH:0.42,fontSize:10.5,align:"center"});
s.addText("면적 항 사전은 q가 이미 0.94~0.99로 포화돼 있다. 이 상태에서 BCE를 가장 빨리 줄이는 길은 과신한 행을 끌어내리는 것인데, 거짓양성이 전부 산 많은 곳이다. 그래서 κ가 음수로 간다 — 순위 개선이 아니라 수준 보정이다.",
  {x:6.25,y:3.9,w:6.4,h:0.94,fontSize:11,color:MUT,lineSpacing:15,fontFace:B,isTextBox:true,margin:0});
s.addShape(pres.ShapeType.roundRect,{x:0.65,y:5.06,w:12.0,h:1.3,rectRadius:0.08,fill:{color:SURF},line:{color:LINE,width:0.5}});
s.addText("결정적 확인 — 가려둔 83행에서 잰 BCE (자기 목적함수인데도 일반화되지 않는다)",
  {x:0.95,y:5.24,w:11.4,h:0.3,fontSize:12,bold:true,color:INK,fontFace:H,isTextBox:true,margin:0});
s.addText("B0 = 0.4322     ·     B2 (ω=4.35) = 0.4548     ·     B2-ω10 = 0.4599         →  정답으로 학습한 조건이 학습하지 않은 조건보다 나쁘다",
  {x:0.95,y:5.64,w:11.4,h:0.56,fontSize:12,color:MUT,lineSpacing:16,fontFace:B,isTextBox:true,margin:0});
s.addNotes("훗카이도 회차만 κ가 양수인 것은 그 회차에서만 훗카이도의 반대되는 라벨이 BCE에서 빠지기 때문이다. κ 부호 불안정의 원인은 학습이 아니라 이 지진 하나다.");

/* ── 13 LQ 결과 ── */
s=pres.addSlide(); s.background={color:WHT};
title(s,"결과 ② 액상화(LQ)","음성이 120개로 LS(20개)보다 여섯 배 많아 그 자체로 더 튼튼한 평가판이다. BCE는 LS에만 걸리고 z_LQ에는 κ가 없다");
tbl(s,[[hd("ID"),hd("사전"),hd("사후"),hd("Δ"),hd("사후 (144)"),hd("LQ MSE")],
 ["A0","0.7154","0.7458","+0.0303","0.8329",bd("0.2184",POS)],
 ["A1","0.7154","0.7454","+0.0300","0.8325","0.2195"],
 ["A2","0.7154","0.7590","+0.0435",bd("0.8437"),"0.2361"],
 [bd("B0",ACC),bd("0.7698",ACC),bd("0.7812",ACC),"+0.0114","0.8435","0.2497"],
 ["B1","0.7698","0.7796","+0.0098","0.8415","0.2504"],
 ["B2","0.7698","0.7806","+0.0108","0.8428","0.2499"],
 [g("C0"),"0.7698",bd("0.8158",POS),bd("+0.0460",POS),bd("0.8604",POS),"0.2399"],
 [g("C2"),"0.7698","0.8153","+0.0455","0.8598",bd("0.2386",POS)]],
 {x:0.65,y:1.66,w:6.0,colW:[0.95,1.02,1.02,1.02,1.09,0.9],rowH:0.335,fontSize:10.5,align:"center"});
s.addText("182 = AUC가 정의되는 6개 지진 전부.  144 = 음성이 20개 이상인 세 개(구마모토 22 · 훗카이도 23 · 노토반도 31).\nLQ 사전이 B·C 전부 0.7698로 같은 것은 b_LQ가 상수라 순위를 못 바꾸고 κ가 LQ 식에 없기 때문이다.",
  {x:0.65,y:4.42,w:6.0,h:0.62,fontSize:10,color:MUT,lineSpacing:13,fontFace:B,isTextBox:true,margin:0});
s.addText("지진별 LQ 사전 → 사후",{x:6.95,y:1.62,w:5.7,h:0.3,fontSize:12,bold:true,color:INK,fontFace:B,isTextBox:true,margin:0});
tbl(s,[[hd("지진"),hd("음성"),hd("B0"),hd("C0")],
 ["2016 구마모토","22","0.9318 → 0.9369",bd("0.9318 → 0.9520",POS)],
 ["2018 훗카이도","23",bd("0.9105 → 0.9156",POS),{text:"0.9105 → 0.8926",options:{color:NEG}}],
 ["2024 노토반도","31","0.7263 → 0.7400",bd("0.7263 → 0.7830",POS)],
 ["2004 니가타현주에쓰","3","0.5167 → 0.5000","0.5167 → 0.5167"],
 [g("2021 후쿠시마"),g("1"),g("0.3333 → 0.5000"),g("0.3333 → 0.8333")],
 [g("2000 돗토리"),g("1"),g("0.7143 → 0.7143"),g("0.7143 → 0.8571")]],
 {x:6.95,y:2.0,w:5.7,colW:[1.95,0.65,1.55,1.55],rowH:0.335,fontSize:10,align:"center"});
s.addShape(pres.ShapeType.roundRect,{x:6.95,y:4.42,w:5.7,h:0.72,rectRadius:0.08,fill:{color:DARK},line:{color:DARK,width:0}});
s.addText("LQ에서는 충돌이 없다 — C0이 Δ도 1위, 절대값도 1위다.",
  {x:7.2,y:4.56,w:5.25,h:0.44,fontSize:11.5,bold:true,color:WHT,lineSpacing:15,fontFace:B,isTextBox:true,margin:0});
s.addText("왜 B 계열의 LQ MSE가 A 계열보다 나쁜가 — LQ 양성비율은 0.476이라 상수만 찍어도 MSE 0.2494가 나온다. B0의 0.2497은 그 기준선과 같고 A0의 0.2184는 그보다 좋다. 원인은 log k_LQ 평균이 6.66이라 q_LQ가 통째로 밀려 중앙값 0.9145가 되는 것인데, 지시서 §2-1 B가 b_LQ를 0으로 못박아 되돌릴 수단이 없었다. C0이 b_LQ = −4.12를 학습해 0.2399로 기준선 아래로 내렸다.",
  {x:0.65,y:5.3,w:12.0,h:1.0,fontSize:11,color:INK,lineSpacing:15,fontFace:B,isTextBox:true,margin:0});
s.addText("순위(AUC)와 확률 수준(MSE)은 따로 봐야 한다.",
  {x:0.65,y:6.36,w:12.0,h:0.3,fontSize:11,bold:true,color:ACC,fontFace:B,isTextBox:true,margin:0});
s.addNotes("신뢰 지진(144)만 보면 A2 0.8437이 B0 0.8435를 아주 근소하게 앞선다. LS에서 밀린 A2가 LQ에서는 B0과 동급이다.");

/* ── 14 사후 탐색 ── */
s=pres.addSlide(); s.background={color:WHT};
title(s,"사후 탐색 — 사전등록 조건표 밖","결과를 본 뒤에 확인한 두 가지다. §5 판정에는 반영하지 않았다");
num(s,0.65,1.6,1,ACC);
s.addText("b_LQ 고정을 푼다",{x:1.15,y:1.58,w:5.3,h:0.32,fontSize:14.5,bold:true,color:INK,fontFace:H,isTextBox:true,margin:0});
s.addText("log k_LQ 평균이 6.66이라 q_LQ가 통째로 밀려 중앙값 0.9145가 된다. 실제 액상화 발생률은 229행 중 0.476이다.",
  {x:0.65,y:1.96,w:5.75,h:0.54,fontSize:10.5,color:MUT,lineSpacing:14,fontFace:B,isTextBox:true,margin:0});
tbl(s,[[hd("지표"),hd("B0  b_LQ=0"),hd("C0  b_LQ 학습")],
 ["LQ 사전 가중","0.7698",g("0.7698")],
 ["LQ 사후 가중","0.7812",bd("0.8158",POS)],
 ["LQ MSE (사후)","0.2497",bd("0.2399",POS)],
 ["q_LQ 중앙값","0.9145",bd("0.1485")],
 ["LS 사전 가중","0.8400",g("0.8400")],
 ["LS 사후 가중","0.8550",g("0.8529")]],
 {x:0.65,y:2.6,w:5.75,colW:[1.95,1.85,1.95],rowH:0.315,fontSize:10.5,align:"center"});
s.addText("사전 순위는 두 지표 모두 그대로다. b_LQ는 모든 행에 더해지는 같은 상수라 순위를 못 바꾼다. 확률 수준만 고쳤는데 사후가 올랐다.",
  {x:0.65,y:4.86,w:5.75,h:0.6,fontSize:10.5,color:INK,lineSpacing:14,fontFace:B,isTextBox:true,margin:0});
num(s,6.85,1.6,2,POS);
s.addText("log k에서 평균을 뺀다",{x:7.35,y:1.58,w:5.3,h:0.32,fontSize:14.5,bold:true,color:INK,fontFace:H,isTextBox:true,margin:0});
s.addText("b를 학습하는 채널에서만 뺀다. b를 고정한 채널에서 빼면 z = log(π̄·k) = log λ 라는 유도식이 깨진다 — B0이 그렇다. 평균은 학습 418행 전체 평균 하나다(LS 8.0422 / LQ 6.6559).",
  {x:6.85,y:1.96,w:5.8,h:0.54,fontSize:10.5,color:MUT,lineSpacing:14,fontFace:B,isTextBox:true,margin:0});
tbl(s,[[hd("조건"),hd("중심화"),hd("b 유효수준"),hd("LS 사후"),hd("LQ 사후")],
 ["B1","한다","−2.4362","0.7285","0.7796"],["B1","안 한다","−2.4309","0.7285","0.7796"],
 ["C0","한다","−4.1139","0.8529","0.8158"],["C0","안 한다","−4.1186","0.8529","0.8158"],
 ["B2","한다","−0.2946","0.8507","0.7807"],["B2","안 한다","−0.2955","0.8507","0.7806"]],
 {x:6.85,y:2.6,w:5.8,colW:[0.85,1.2,1.5,1.13,1.12],rowH:0.315,fontSize:10.5,align:"center"});
s.addText("최적해가 같다 — 소수 셋째 자리까지 일치한다. 차이는 b의 해석과 조건수뿐이다. 단 상자를 함께 열어야 한다.",
  {x:6.85,y:4.86,w:5.8,h:0.6,fontSize:10.5,color:INK,lineSpacing:14,fontFace:B,isTextBox:true,margin:0});
s.addShape(pres.ShapeType.roundRect,{x:0.65,y:5.56,w:12.0,h:1.08,rectRadius:0.08,fill:{color:DARK},line:{color:DARK,width:0}});
s.addText("① b_LQ 해제는 LQ를 0.7812 → 0.8158로 올렸다 (짝지은 부트스트랩 3,000회, P = 0.978).      ② 중심화는 성능 장치가 아니라 해석·수치 안정성을 위한 매개변수화 선택이다.",
  {x:0.95,y:5.72,w:11.4,h:0.36,fontSize:11,color:WHT,fontFace:B,isTextBox:true,margin:0});
s.addText("기존 상자 [−2, 4]는 실제로 걸리고 있었고(B1의 b_LS가 하한 −2에 붙음), 중심화하면 LS는 b가 +8.21까지 가야 해 상한 4에 닿지 못한다. 켤 때는 상자도 함께 연다.",
  {x:0.95,y:6.12,w:11.4,h:0.36,fontSize:11,color:"C3CFD6",fontFace:B,isTextBox:true,margin:0});
s.addNotes("두 가지 모두 결과를 본 뒤에 나온 아이디어라 판정표에는 섞지 않고 별도 파일로 분리했다.");

/* ── 15 결론 ── */
s=pres.addSlide(); s.background={color:DARK};
s.addText("결론 — 무엇을 적용할까",{x:0.85,y:0.58,w:11.6,h:0.6,fontSize:31,bold:true,color:WHT,fontFace:H,isTextBox:true,margin:0});
s.addText("사전등록 기준 1위와, 사후 탐색까지 포함한 1위를 나란히 둔다.",
  {x:0.85,y:1.22,w:11.6,h:0.34,fontSize:13,color:"8B9BA6",fontFace:B,isTextBox:true,margin:0});
s.addShape(pres.ShapeType.roundRect,{x:0.85,y:1.78,w:5.7,h:3.95,rectRadius:0.08,fill:{color:DARK2},line:{color:ACC_L,width:1.5}});
s.addText("B0   사전등록 기준 1위",{x:1.15,y:1.96,w:5.1,h:0.34,fontSize:15.5,bold:true,color:ACC_L,fontFace:H,isTextBox:true,margin:0});
s.addText("z_LS = log(π̄_LS) + log k_LS\nz_LQ = log(π̄_LQ) + log k_LQ\nκ 없음 · ω = 0 · b 전부 0 고정 · 평균 안 뺌",
  {x:1.15,y:2.4,w:5.1,h:1.0,fontSize:12,color:WHT,lineSpacing:18,fontFace:B,isTextBox:true,margin:0});
[["LS 사전 가중","0.8400"],["LS 사후 가중","0.8550"],["LQ 사전 가중","0.7698"],["LQ 사후 가중","0.7812"],
 ["LS MSE (사후)","0.1343"],["사전 학습 파라미터","0개"]].forEach(([k,v],i)=>{
  s.addText(k,{x:1.15,y:3.5+i*0.345,w:2.9,h:0.3,fontSize:10.5,color:"8B9BA6",fontFace:B,isTextBox:true,margin:0});
  s.addText(v,{x:4.2,y:3.5+i*0.345,w:2.1,h:0.3,fontSize:11.5,bold:true,color:WHT,align:"right",fontFace:B,isTextBox:true,margin:0});
});
s.addShape(pres.ShapeType.roundRect,{x:6.95,y:1.78,w:5.5,h:3.95,rectRadius:0.08,fill:{color:DARK2},line:{color:POS_L,width:1.5}});
s.addText("C0   사후 탐색 포함 1위",{x:7.25,y:1.96,w:4.9,h:0.34,fontSize:15.5,bold:true,color:POS_L,fontFace:H,isTextBox:true,margin:0});
s.addText("B0과 같되 b_LQ만 학습한다 (−4.12로 수렴)\nLS 식은 B0과 글자 하나 다르지 않다\n→ LS 사전확률 최대 절대차 0.00e+00",
  {x:7.25,y:2.4,w:4.9,h:1.0,fontSize:12,color:WHT,lineSpacing:18,fontFace:B,isTextBox:true,margin:0});
[["LS 사전 가중","0.8400"],["LS 사후 가중","0.8529"],["LQ 사전 가중","0.7698"],["LQ 사후 가중","0.8158"],
 ["LS MSE (사후)","0.1338"],["사전 학습 파라미터","1개"]].forEach(([k,v],i)=>{
  s.addText(k,{x:7.25,y:3.5+i*0.345,w:2.8,h:0.3,fontSize:10.5,color:"8B9BA6",fontFace:B,isTextBox:true,margin:0});
  s.addText(v,{x:10.1,y:3.5+i*0.345,w:2.05,h:0.3,fontSize:11.5,bold:true,color:(i===3||i===4)?POS_L:WHT,align:"right",fontFace:B,isTextBox:true,margin:0});
});
s.addText("발표에서는 B0을 주 결과로 두고, A2는 “제안하신 LOEO 절차는 A 계열에서 유의하게 작동했으나(+0.0817, P=0.98), 면적 항이 이미 같은 정보를 담고 있어 B 계열에서는 추가 이득이 없었다”로 방법 검증 결과에 배치하는 것을 권한다. C0은 다음 실험 제안으로 붙인다.",
  {x:0.85,y:5.94,w:11.6,h:0.92,fontSize:11.5,color:"C3CFD6",lineSpacing:16,fontFace:B,isTextBox:true,margin:0});
s.addNotes("가장 좋은 결과가 가장 적게 학습한 구성이라는 점이 이번 실험의 핵심 메시지다.");

/* ── 16 한계와 다음 ── */
s=pres.addSlide(); s.background={color:WHT};
title(s,"한계와 다음 단계","숫자를 어디까지 믿을 수 있는지부터 적는다");
s.addText("한계",{x:0.65,y:1.58,w:5.9,h:0.3,fontSize:13,bold:true,color:NEG,fontFace:B,isTextBox:true,margin:0});
[["LS 음성이 20개뿐이다","지진 안 양성–음성 쌍이 전부 합쳐 275쌍이다. 2018 오사카의 1.0000은 10쌍짜리다."],
 ["최고 기록은 새 값이 아니다","B0의 0.8550은 기존 자료의 0.855와 같다. 이번 실험에서 그것을 넘은 조건은 없었다."],
 ["A1이 발표자료 12쪽 ③과 어긋난다","LS 0.7479(기대 0.717), κ 0.2795(기대 0.05). 확인이 필요하다."],
 ["훗카이도 라벨을 다시 볼 필요가 있다","히다카초·유바리시의 ls_flag=0이 ‘없음’인지 ‘집계 항목 없음’인지 원자료 확인."]]
 .forEach(([t,d],i)=>{
  const y=1.94+i*1.14; card(s,0.65,y,5.9,1.0);
  s.addShape(pres.ShapeType.ellipse,{x:0.92,y:y+0.18,w:0.19,h:0.19,fill:{color:NEG},line:{color:NEG,width:0}});
  s.addText(t,{x:1.25,y:y+0.13,w:5.05,h:0.28,fontSize:11.5,bold:true,color:INK,fontFace:B,isTextBox:true,margin:0});
  s.addText(d,{x:1.25,y:y+0.42,w:5.05,h:0.5,fontSize:10.5,color:MUT,lineSpacing:13,fontFace:B,isTextBox:true,margin:0});
});
s.addText("다음 단계",{x:6.75,y:1.58,w:5.9,h:0.3,fontSize:13,bold:true,color:POS,fontFace:B,isTextBox:true,margin:0});
[["병목은 사전이 아니라 우도다","B0은 음성 충분한 세 지진에서 사전=사후(0.8177)이고 A0은 사전을 0.075 깎는다. 채널별로 끄고 재본다."],
 ["감독 대상을 산지 말고 다른 변수로","면적 항이 아직 모르는 정보 — 경사도, 지질, 강우 — 쪽이어야 한다."],
 ["b_LQ 건을 정식 조건으로 사전등록","이번에는 사후 탐색으로만 확인했다. 조건을 미리 고정하고 다시 돌린다."],
 ["B에서 κ를 쓰려면 부호 제약(κ ≥ 0)","강제 κ=+1이 사전을 0.8539로 올린다. 다만 결과를 보고 나온 가설이라 별도 사전등록이 필요하다."]]
 .forEach(([t,d],i)=>{
  const y=1.94+i*1.14; card(s,6.75,y,5.9,1.0);
  num(s,6.93,y+0.3,i+1,POS);
  s.addText(t,{x:7.5,y:y+0.13,w:4.95,h:0.28,fontSize:11.5,bold:true,color:INK,fontFace:B,isTextBox:true,margin:0});
  s.addText(d,{x:7.5,y:y+0.42,w:4.95,h:0.5,fontSize:10.5,color:MUT,lineSpacing:13,fontFace:B,isTextBox:true,margin:0});
});
s.addText("산출물 — results/loeo/LOEO_결과.xlsx (7시트) · results/posthoc/사후탐색_결과.xlsx · 브랜치 claude/vigilant-wozniak-atum1b",
  {x:0.65,y:6.6,w:12.0,h:0.32,fontSize:10,color:MUT,italic:true,fontFace:B,isTextBox:true,margin:0});
s.addNotes("한계를 먼저 적는 것이 중요하다. 특히 음성 20개라는 표본 제약은 모든 LS 숫자에 걸린다.");

pres.writeFile({fileName: process.argv[2]}).then(f=>console.log("작성:",f));
