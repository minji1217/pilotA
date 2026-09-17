const pptxgen=require("pptxgenjs");
const pres=new pptxgen(); pres.layout="LAYOUT_WIDE";
pres.title="교수님 제안 검증 결과";

const DARK="16212A",DARK2="22313C",ACC="1D4E6B",ACC_L="5A8CA8",SOFT="E4EDF2",
      POS="2F7150",POS_L="7FB79A",NEG="A8442E",NEG_L="D9A192",SURF="EEF2F4",
      LINE="D6DEE3",MUT="6B7A84",INK="16212A",WHT="FFFFFF";
const H="Cambria",B="Calibri";
const T=(s,t,sub)=>{
  s.addText(t,{x:0.75,y:0.48,w:11.8,h:0.7,fontSize:31,bold:true,color:INK,fontFace:H,isTextBox:true,margin:0});
  if(sub) s.addText(sub,{x:0.75,y:1.24,w:11.8,h:0.4,fontSize:15,color:MUT,fontFace:B,isTextBox:true,margin:0});
};
const card=(s,x,y,w,h,f,l,lw)=>s.addShape(pres.ShapeType.roundRect,{x,y,w,h,rectRadius:0.1,
  fill:{color:f||SURF},line:{color:l||LINE,width:lw||(l?1.5:0.5)}});

// 2 x 3 실험 격자 — 3장과 4장이 같은 자리를 쓴다
const COLS=["아무것도 안 함","산지 항만 넣음\n(정답 학습 없음)","산지 항 + 정답 학습\n(교수님 제안)"];
const ROWS=["면적 항 없음\n(기존 방식)","면적 항 있음\n(USGS 값 × 칸 수)"];
const gridFrame=(s)=>{
  COLS.forEach((c,i)=>s.addText(c,{x:3.3+i*3.1,y:1.94,w:2.95,h:0.56,fontSize:12.5,bold:true,
    color:INK,align:"center",lineSpacing:16,fontFace:B,isTextBox:true,margin:0}));
  ROWS.forEach((r,j)=>s.addText(r,{x:0.75,y:2.66+j*1.5,w:2.4,h:1.1,fontSize:12.5,bold:true,
    color:ACC,valign:"middle",lineSpacing:17,fontFace:B,isTextBox:true,margin:0}));
};
const cellXY=(r,c)=>[3.3+c*3.1,2.56+r*1.5];

/* ── 1 표지 ── */
let s=pres.addSlide(); s.background={color:DARK};
s.addText("후속실험 3 · 핵심 요약",{x:1.0,y:1.7,w:8,h:0.36,fontSize:13.5,color:ACC_L,bold:true,charSpacing:2.5,fontFace:B,isTextBox:true,margin:0});
s.addText("교수님 제안 검증 결과",{x:1.0,y:2.16,w:9,h:0.9,fontSize:42,bold:true,color:WHT,fontFace:H,isTextBox:true,margin:0});
s.addText("산사태 정답을 학습에도 쓰고, 지진을 하나씩 가려 평가했다",
  {x:1.0,y:3.14,w:9,h:0.42,fontSize:16,color:"C3CFD6",fontFace:B,isTextBox:true,margin:0});
s.addShape(pres.ShapeType.line,{x:1.0,y:3.96,w:2.6,h:0,line:{color:ACC_L,width:2.5}});
s.addText("결론 — 제안은 작동했다. 단, 면적 항이 없을 때만.",
  {x:1.0,y:4.2,w:10,h:0.5,fontSize:21,bold:true,color:ACC_L,fontFace:H,isTextBox:true,margin:0});
s.addText("실험 30회 · LOEO 5회차 · 부트스트랩 3,000회 · 판정 기준은 결과 확인 전에 고정",
  {x:1.0,y:4.84,w:10,h:0.4,fontSize:12.5,color:"8B9BA6",fontFace:B,isTextBox:true,margin:0});

/* ── 2 제안 → 적용 ── */
s=pres.addSlide(); s.background={color:WHT};
T(s,"① 교수님 제안과 우리가 적용한 것");
card(s,0.75,1.86,5.7,2.5,SOFT,ACC);
s.addText("교수님 제안",{x:1.05,y:2.06,w:5.1,h:0.3,fontSize:12.5,bold:true,color:ACC,charSpacing:1,fontFace:B,isTextBox:true,margin:0});
s.addText("“산사태 정답을 학습에도 쓰되,\n공정하게 평가하려고\n지진을 하나씩 가려서 시험해라.”",
  {x:1.05,y:2.44,w:5.1,h:1.1,fontSize:16,bold:true,color:INK,lineSpacing:24,fontFace:H,isTextBox:true,margin:0});
s.addText("배경 — 산지 비율은 단독으로 0.806을 맞히는데, 모델에 넣으면 계수가 0.05로 거의 학습되지 않았다.",
  {x:1.05,y:3.66,w:5.1,h:0.56,fontSize:11.5,color:MUT,lineSpacing:15,fontFace:B,isTextBox:true,margin:0});
s.addText("우리가 적용한 것",{x:6.9,y:1.86,w:5.6,h:0.3,fontSize:12.5,bold:true,color:INK,charSpacing:1,fontFace:B,isTextBox:true,margin:0});
[["사전확률 식에 산지 항을 넣었다","기존 식 + κ × 산지 비율"],
 ["loss에 산사태 정답을 넣었다","기존 loss + ω × BCE(사전확률, 정답)"],
 ["지진 하나씩 가려 평가했다","5개 지진 × 5회차, 회차마다 처음부터 재학습"]]
 .forEach(([t,d],i)=>{
  const y=2.24+i*0.74;
  s.addShape(pres.ShapeType.ellipse,{x:6.9,y:y+0.08,w:0.34,h:0.34,fill:{color:ACC},line:{color:ACC,width:0}});
  s.addText(String(i+1),{x:6.9,y:y+0.08,w:0.34,h:0.34,fontSize:13,bold:true,color:WHT,align:"center",valign:"middle",fontFace:H,isTextBox:true,margin:0});
  s.addText(t,{x:7.42,y:y,w:5.1,h:0.3,fontSize:14,bold:true,color:INK,fontFace:B,isTextBox:true,margin:0});
  s.addText(d,{x:7.42,y:y+0.3,w:5.1,h:0.3,fontSize:11.5,color:MUT,fontFace:B,isTextBox:true,margin:0});
});
s.addShape(pres.ShapeType.roundRect,{x:0.75,y:4.62,w:11.75,h:1.1,rectRadius:0.1,fill:{color:DARK},line:{color:DARK,width:0}});
s.addText("그리고 이것을 두 가지 사전확률 위에서 각각 돌렸다",
  {x:1.05,y:4.78,w:11.2,h:0.34,fontSize:15,bold:true,color:ACC_L,fontFace:H,isTextBox:true,margin:0});
s.addText("① 기존 방식  —  USGS 값을 그대로 쓴다          ② 면적 항 —  USGS 값 × 칸 수 (26.09.16 작업에서 이미 확정된 기준선)",
  {x:1.05,y:5.16,w:11.2,h:0.36,fontSize:13,color:"C3CFD6",fontFace:B,isTextBox:true,margin:0});

/* ── 3 돌린 실험 ── */
s=pres.addSlide(); s.background={color:WHT};
T(s,"② 돌린 실험","6개 조건을 이렇게 짰다. 각 칸이 하나의 조건이다");
gridFrame(s);
[[0,0,"기준선","1회"],[0,1,"비교용","1회"],[0,2,"제안 적용","5회차"],
 [1,0,"기준선","1회"],[1,1,"비교용","1회"],[1,2,"제안 적용","5회차"]]
 .forEach(([r,c,lab,run])=>{
  const [x,y]=cellXY(r,c); const key=(c===2);
  card(s,x,y,2.95,1.3,key?SOFT:WHT,key?ACC:LINE);
  s.addText(lab,{x:x+0.1,y:y+0.3,w:2.75,h:0.34,fontSize:14,bold:true,color:key?ACC:MUT,align:"center",fontFace:H,isTextBox:true,margin:0});
  s.addText(run,{x:x+0.1,y:y+0.68,w:2.75,h:0.3,fontSize:12,color:MUT,align:"center",fontFace:B,isTextBox:true,margin:0});
});
s.addText("＋ 민감도 확인 — BCE 가중치 ω를 1·10으로, 링크 함수를 logit으로 바꿔 각각 다시.  합계 30회.",
  {x:0.75,y:5.7,w:11.8,h:0.34,fontSize:13,color:MUT,fontFace:B,isTextBox:true,margin:0});
s.addShape(pres.ShapeType.roundRect,{x:0.75,y:6.12,w:11.75,h:0.72,rectRadius:0.1,fill:{color:SURF},line:{color:LINE,width:0.5}});
s.addText("공정성 장치 — 조건·ω·성공 기준을 결과 확인 전에 고정 · 가린 지진에서만 채점 · 짝지은 부트스트랩 3,000회로 비교 · 기존 결과 재현 확인(±0.0000)",
  {x:1.0,y:6.3,w:11.25,h:0.36,fontSize:12,bold:true,color:INK,fontFace:B,isTextBox:true,margin:0});

/* ── 4 결과 ── */
s=pres.addSlide(); s.background={color:WHT};
T(s,"③ 실험 결과","같은 자리에 점수를 넣었다. 숫자는 산사태 예측 점수(1.0이 완벽, 0.5가 찍기)");
gridFrame(s);
[[0,0,"0.722",MUT,"",false],[0,1,"0.748",MUT,"",false],[0,2,"0.804",POS,"제안이 올렸다   ＋0.082",true],
 [1,0,"0.855",ACC,"전체 1위",true],[1,1,"0.729",NEG,"크게 떨어졌다",false],[1,2,"0.851",NEG,"오르지 않았다   －0.004",false]]
 .forEach(([r,c,v,col,note,win])=>{
  const [x,y]=cellXY(r,c);
  card(s,x,y,2.95,1.3,WHT,win?col:LINE,win?2:0.5);
  s.addText(v,{x:x+0.1,y:y+0.14,w:2.75,h:0.68,fontSize:36,bold:true,color:col,align:"center",fontFace:H,isTextBox:true,margin:0});
  if(note) s.addText(note,{x:x+0.08,y:y+0.86,w:2.79,h:0.34,fontSize:11.5,bold:true,color:col,align:"center",fontFace:B,isTextBox:true,margin:0});
});
card(s,0.75,5.66,5.7,1.18,"EDF3EF",POS);
s.addText("면적 항이 없으면 — 제안이 통했다",{x:1.02,y:5.8,w:5.2,h:0.3,fontSize:13.5,bold:true,color:POS,fontFace:H,isTextBox:true,margin:0});
s.addText("0.722 → 0.804. 우연일 확률 2% 미만.\n다섯 회차 모두 “산이 많으면 산사태가 많다”로 학습됐다.",
  {x:1.02,y:6.14,w:5.2,h:0.56,fontSize:11.5,color:MUT,lineSpacing:15,fontFace:B,isTextBox:true,margin:0});
card(s,6.8,5.66,5.7,1.18,"F7EDEA",NEG);
s.addText("면적 항이 있으면 — 통하지 않았다",{x:7.07,y:5.8,w:5.2,h:0.3,fontSize:13.5,bold:true,color:NEG,fontFace:H,isTextBox:true,margin:0});
s.addText("0.855 → 0.851. 다시 뽑은 3,000개 표본 전부에서 못 넘었다.\n단, 정답 없이 산지만 넣으면 0.729로 망가진다 — 정답 학습이 그걸 막아준 것이다.",
  {x:7.07,y:6.14,w:5.2,h:0.56,fontSize:11.5,color:MUT,lineSpacing:15,fontFace:B,isTextBox:true,margin:0});

/* ── 5 왜 ── */
s=pres.addSlide(); s.background={color:WHT};
T(s,"④ 왜 면적 항 위에서는 통하지 않았나","칸 수와 산지 비율이 사실 같은 것을 재고 있었다");
s.addShape(pres.ShapeType.ellipse,{x:1.5,y:2.1,w:3.1,h:3.1,fill:{color:ACC,transparency:62},line:{color:ACC,width:1.5}});
s.addShape(pres.ShapeType.ellipse,{x:3.4,y:2.1,w:3.1,h:3.1,fill:{color:POS,transparency:62},line:{color:POS,width:1.5}});
s.addText("칸 수\n(시정촌 면적)",{x:1.15,y:3.25,w:1.85,h:0.8,fontSize:13,bold:true,color:ACC,align:"center",lineSpacing:18,fontFace:B,isTextBox:true,margin:0});
s.addText("산지 비율",{x:4.95,y:3.47,w:1.6,h:0.36,fontSize:13,bold:true,color:POS,align:"center",fontFace:B,isTextBox:true,margin:0});
s.addText("겹침\n0.53",{x:3.6,y:3.25,w:0.8,h:0.8,fontSize:15,bold:true,color:INK,align:"center",lineSpacing:19,fontFace:H,isTextBox:true,margin:0});
s.addText("산이 많은 곳은 대체로 넓은 시정촌이다",{x:1.1,y:5.34,w:5.8,h:0.36,fontSize:13.5,bold:true,color:INK,align:"center",fontFace:B,isTextBox:true,margin:0});
card(s,7.3,2.1,5.2,3.1);
s.addText("도착지가 거의 같았다",{x:7.6,y:2.32,w:4.6,h:0.32,fontSize:13.5,bold:true,color:ACC,fontFace:H,isTextBox:true,margin:0});
s.addText("정답을 학습해서 도달한 사전확률 점수",{x:7.6,y:2.78,w:4.6,h:0.3,fontSize:12,color:MUT,fontFace:B,isTextBox:true,margin:0});
s.addText("0.834",{x:7.6,y:3.08,w:4.6,h:0.56,fontSize:30,bold:true,color:POS,fontFace:H,isTextBox:true,margin:0});
s.addText("칸 수를 곱해서 얻은 사전확률 점수",{x:7.6,y:3.82,w:4.6,h:0.3,fontSize:12,color:MUT,fontFace:B,isTextBox:true,margin:0});
s.addText("0.840",{x:7.6,y:4.12,w:4.6,h:0.56,fontSize:30,bold:true,color:ACC,fontFace:H,isTextBox:true,margin:0});
s.addText("서로 다른 길로 같은 정보에 닿았다.",{x:7.6,y:4.82,w:4.6,h:0.3,fontSize:12.5,bold:true,color:INK,fontFace:B,isTextBox:true,margin:0});
s.addShape(pres.ShapeType.roundRect,{x:0.75,y:5.92,w:11.75,h:0.92,rectRadius:0.1,fill:{color:DARK},line:{color:DARK,width:0}});
s.addText("이미 아는 것을 다시 가르칠 수는 없다 — 면적 항이 산지 정보를 이미 담고 있어, 그 위에서는 산지 항이 더 보탤 것이 없었다.",
  {x:1.05,y:6.18,w:11.2,h:0.4,fontSize:14,bold:true,color:WHT,fontFace:H,isTextBox:true,margin:0});

/* ── 6 결론 ── */
s=pres.addSlide(); s.background={color:DARK};
s.addText("⑤ 결론",{x:0.9,y:0.6,w:11.6,h:0.62,fontSize:31,bold:true,color:WHT,fontFace:H,isTextBox:true,margin:0});
s.addShape(pres.ShapeType.roundRect,{x:0.9,y:1.5,w:11.6,h:1.46,rectRadius:0.1,fill:{color:DARK2},line:{color:ACC_L,width:1.5}});
s.addText("쓸 것 — USGS 값 × 칸 수",{x:1.25,y:1.7,w:6.5,h:0.5,fontSize:24,bold:true,color:WHT,fontFace:H,isTextBox:true,margin:0});
s.addText("산지 항 없음 · 산사태 정답 미사용 · 사전확률에 학습할 값이 하나도 없다",
  {x:1.25,y:2.26,w:7.0,h:0.34,fontSize:13,color:"C3CFD6",fontFace:B,isTextBox:true,margin:0});
s.addText("0.855",{x:8.6,y:1.76,w:1.9,h:0.72,fontSize:38,bold:true,color:ACC_L,align:"center",fontFace:H,isTextBox:true,margin:0});
s.addText("산사태",{x:8.6,y:2.46,w:1.9,h:0.3,fontSize:11.5,color:"8B9BA6",align:"center",fontFace:B,isTextBox:true,margin:0});
s.addText("0.781",{x:10.5,y:1.76,w:1.9,h:0.72,fontSize:38,bold:true,color:WHT,align:"center",fontFace:H,isTextBox:true,margin:0});
s.addText("액상화",{x:10.5,y:2.46,w:1.9,h:0.3,fontSize:11.5,color:"8B9BA6",align:"center",fontFace:B,isTextBox:true,margin:0});
s.addText("교수님께 드릴 답",{x:0.9,y:3.2,w:11.6,h:0.32,fontSize:13.5,bold:true,color:ACC_L,fontFace:B,isTextBox:true,margin:0});
s.addShape(pres.ShapeType.roundRect,{x:0.9,y:3.56,w:11.6,h:1.32,rectRadius:0.1,fill:{color:DARK2},line:{color:"31424F",width:0.75}});
s.addText("“제안하신 절차는 기존 방식 위에서 유의하게 작동했습니다 (0.722 → 0.804, 우연일 확률 2% 미만).\n다만 칸 수를 곱하는 수정이 산지 비율과 같은 정보를 이미 담고 있어(겹침 0.53) 그 위에서는 추가 이득이 없었습니다.\n감독 구조는 유지하고, 칸 수가 아직 모르는 변수로 대상을 바꿔볼 차례입니다.”",
  {x:1.2,y:3.74,w:11.0,h:1.0,fontSize:13,color:WHT,lineSpacing:20,fontFace:B,isTextBox:true,margin:0});
s.addText("다음에 할 것",{x:0.9,y:5.14,w:11.6,h:0.32,fontSize:13.5,bold:true,color:ACC_L,fontFace:B,isTextBox:true,margin:0});
[["감독 대상을 바꾼다","경사도 · 지질 · 강우 — 칸 수가 모르는 변수로"],
 ["회귀 모델을 들여다본다","지금 산사태 순서에 거의 기여하지 못하고 있다"],
 ["훗카이도 라벨을 확인한다","산지 비율이 거꾸로 작동하는 유일한 지진이다"]]
 .forEach(([t,d],i)=>{
  const x=0.9+i*3.92;
  s.addShape(pres.ShapeType.roundRect,{x,y:5.5,w:3.72,h:1.06,rectRadius:0.1,fill:{color:DARK2},line:{color:"31424F",width:0.75}});
  s.addText(t,{x:x+0.25,y:5.64,w:3.25,h:0.3,fontSize:12.5,bold:true,color:WHT,fontFace:B,isTextBox:true,margin:0});
  s.addText(d,{x:x+0.25,y:5.94,w:3.25,h:0.5,fontSize:11,color:"8B9BA6",lineSpacing:14,fontFace:B,isTextBox:true,margin:0});
});
s.addText("솔직히 — 0.855는 이미 갖고 있던 값이다. 이번 실험에서 새로 얻은 것은 “왜 그 값을 넘지 못하는가”에 대한 답이다.",
  {x:0.9,y:6.72,w:11.6,h:0.32,fontSize:11.5,color:"8B9BA6",italic:true,fontFace:B,isTextBox:true,margin:0});

pres.writeFile({fileName:process.argv[2]}).then(f=>console.log("작성:",f));
