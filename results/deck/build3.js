const pptxgen = require("pptxgenjs");
const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE";
pres.title = "산사태 예측 실험 정리";

const DARK="16212A", DARK2="22313C", ACC="1D4E6B", ACC_L="5A8CA8", SOFT="E4EDF2",
      POS="2F7150", POS_L="7FB79A", NEG="A8442E", NEG_L="D9A192", SURF="EEF2F4",
      LINE="D6DEE3", MUT="6B7A84", INK="16212A", WHT="FFFFFF";
const H="Cambria", B="Calibri";

const T=(s,big,small)=>{
  s.addText(big,{x:0.7,y:0.46,w:11.9,h:0.72,fontSize:30,bold:true,color:INK,fontFace:H,isTextBox:true,margin:0});
  if(small) s.addText(small,{x:0.7,y:1.22,w:11.9,h:0.4,fontSize:14.5,color:MUT,fontFace:B,isTextBox:true,margin:0});
};
const card=(s,x,y,w,h,f,l)=>s.addShape(pres.ShapeType.roundRect,{x,y,w,h,rectRadius:0.1,
  fill:{color:f||SURF},line:{color:l||LINE,width:l?1.5:0.5}});
// 큰 숫자 타일
const stat=(s,x,y,w,val,lab,col,sub)=>{
  card(s,x,y,w,1.72,WHT,col);
  s.addText(val,{x:x+0.05,y:y+0.2,w:w-0.1,h:0.78,fontSize:46,bold:true,color:col,align:"center",fontFace:H,isTextBox:true,margin:0});
  s.addText(lab,{x:x+0.15,y:y+1.02,w:w-0.3,h:0.32,fontSize:13,bold:true,color:INK,align:"center",fontFace:B,isTextBox:true,margin:0});
  if(sub) s.addText(sub,{x:x+0.15,y:y+1.34,w:w-0.3,h:0.3,fontSize:11,color:MUT,align:"center",fontFace:B,isTextBox:true,margin:0});
};
const arrow=(s,x,y)=>s.addText("→",{x,y,w:0.8,h:0.6,fontSize:34,bold:true,color:MUT,align:"center",valign:"middle",fontFace:H,isTextBox:true,margin:0});

/* ─────────── 1 표지 ─────────── */
let s=pres.addSlide(); s.background={color:DARK};
s.addText("쉽게 읽는 정리",{x:1.0,y:1.85,w:8,h:0.36,fontSize:14,color:ACC_L,bold:true,charSpacing:2.5,fontFace:B,isTextBox:true,margin:0});
s.addText("산사태가 날 곳을\n어떻게 더 잘 맞혔나",{x:1.0,y:2.35,w:8.6,h:1.9,fontSize:42,bold:true,color:WHT,lineSpacing:52,fontFace:H,isTextBox:true,margin:0});
s.addShape(pres.ShapeType.line,{x:1.0,y:4.5,w:2.6,h:0,line:{color:ACC_L,width:2.5}});
s.addText("파일럿 A · 후속실험 3  ·  실험 60회 정리",{x:1.0,y:4.72,w:8.6,h:0.4,fontSize:14,color:"9AA9B2",fontFace:B,isTextBox:true,margin:0});
s.addNotes("이 발표는 숫자를 나열하지 않고, 무엇을 알아냈는지 순서대로만 이야기한다.");

/* ─────────── 2 결론부터 ─────────── */
s=pres.addSlide(); s.background={color:WHT};
T(s,"먼저 결론 세 줄","자세한 근거는 뒤에서 하나씩 보여드립니다");
[["USGS 값을 쓰는 방법이 틀려 있었다","고치니 0.797 → 0.840 으로 올랐다. 학습을 하나도 안 하고, 엑셀 열 두 개를 곱해서.",ACC],
 ["교수님 제안은 작동했다 — 단, 그 수정을 안 했을 때만","기존 방식에서는 0.722 → 0.804 로 크게 올랐다. 그런데 수정을 한 뒤에는 더 오르지 않았다.",POS],
 ["결국 가장 좋은 건 가장 단순한 것이었다","0.855. 산사태 정답을 한 번도 쓰지 않고, 사전확률에 학습할 값이 하나도 없는 모델이다.",ACC]]
 .forEach(([t,d,c],i)=>{
  const y=1.9+i*1.62; card(s,0.7,y,11.9,1.4);
  s.addShape(pres.ShapeType.ellipse,{x:1.0,y:y+0.36,w:0.62,h:0.62,fill:{color:c},line:{color:c,width:0}});
  s.addText(String(i+1),{x:1.0,y:y+0.36,w:0.62,h:0.62,fontSize:24,bold:true,color:WHT,align:"center",valign:"middle",fontFace:H,isTextBox:true,margin:0});
  s.addText(t,{x:1.9,y:y+0.24,w:10.4,h:0.42,fontSize:19,bold:true,color:INK,fontFace:H,isTextBox:true,margin:0});
  s.addText(d,{x:1.9,y:y+0.7,w:10.4,h:0.4,fontSize:13.5,color:MUT,fontFace:B,isTextBox:true,margin:0});
});
s.addNotes("세 줄이 이 발표의 전부다. 뒤는 이 세 줄의 근거다.");

/* ─────────── 3 무엇을 맞히려는 건가 ─────────── */
s=pres.addSlide(); s.background={color:WHT};
T(s,"우리가 맞히려는 것","“어느 시정촌에서 산사태가 났는가”의 순서를 맞힌다");
card(s,0.7,1.88,5.75,2.5);
s.addText("하는 일",{x:1.0,y:2.08,w:5.2,h:0.32,fontSize:13,bold:true,color:ACC,fontFace:B,isTextBox:true,margin:0});
s.addText("시정촌마다 “산사태가 날 것 같은 정도”를\n숫자로 매긴다. 그 숫자로 줄을 세웠을 때\n실제로 산사태가 난 곳이 위에 오면 잘한 것이다.",
  {x:1.0,y:2.46,w:5.2,h:1.1,fontSize:14,color:INK,lineSpacing:22,fontFace:B,isTextBox:true,margin:0});
s.addText("정확한 확률값을 맞히는 게 아니라 순서를 맞히는 문제다.",
  {x:1.0,y:3.7,w:5.2,h:0.5,fontSize:12,color:MUT,fontFace:B,isTextBox:true,margin:0});
card(s,6.85,1.88,5.75,2.5,SOFT,ACC);
s.addText("점수 읽는 법 — AUC",{x:7.15,y:2.08,w:5.2,h:0.32,fontSize:13,bold:true,color:ACC,fontFace:B,isTextBox:true,margin:0});
[["0.5","동전 던지기와 같음"],["0.8","꽤 잘 맞힘"],["1.0","완벽하게 줄 세움"]].forEach(([v,l],i)=>{
  s.addText(v,{x:7.15,y:2.5+i*0.58,w:0.9,h:0.42,fontSize:22,bold:true,color:i===2?POS:(i===0?NEG:ACC),fontFace:H,isTextBox:true,margin:0});
  s.addText(l,{x:8.2,y:2.58+i*0.58,w:4.2,h:0.34,fontSize:13.5,color:INK,fontFace:B,isTextBox:true,margin:0});
});
s.addShape(pres.ShapeType.roundRect,{x:0.7,y:4.66,w:11.9,h:1.65,rectRadius:0.1,fill:{color:DARK},line:{color:DARK,width:0}});
s.addText("채점 규칙 — 지진 안에서만 줄을 세운다",{x:1.0,y:4.86,w:11.3,h:0.36,fontSize:15,bold:true,color:ACC_L,fontFace:H,isTextBox:true,margin:0});
s.addText("구마모토 지진의 시정촌끼리, 훗카이도 지진의 시정촌끼리 따로 줄을 세우고 점수를 낸 뒤 합친다.\n지진마다 흔들린 세기가 달라서 섞으면 공정하지 않기 때문이다.",
  {x:1.0,y:5.3,w:11.3,h:0.8,fontSize:13.5,color:"C3CFD6",lineSpacing:20,fontFace:B,isTextBox:true,margin:0});
s.addNotes("AUC는 '양성 하나와 음성 하나를 뽑았을 때 양성이 더 높은 점수를 받을 확률'이다. 0.5가 찍기, 1.0이 완벽이다.");

/* ─────────── 4 출발점 ─────────── */
s=pres.addSlide(); s.background={color:WHT};
T(s,"출발점 — USGS가 주는 값을 그대로 쓰면","미국 지질조사국(USGS)이 지진마다 “산사태 위험도” 값을 제공한다");
stat(s,1.2,2.2,3.0,"0.797","USGS 값 그대로",MUT,"기존 출발점");
s.addText("이 값 하나로도 꽤 맞힌다. 하지만 두 가지가 아쉬웠다.",
  {x:5.0,y:2.3,w:7.4,h:0.38,fontSize:15,bold:true,color:INK,fontFace:H,isTextBox:true,margin:0});
[["산지 비율을 넣으면 오히려 나빠졌다","산이 많은 곳에 산사태가 나는 게 당연한데, 회귀식에 넣으면 점수가 0.651로 떨어졌다."],
 ["피해 건수로 학습해도 좋아지지 않았다","사망·전파 같은 피해 건수로 3000번 학습해도 산사태 순서가 오히려 0.722로 깎였다."]]
 .forEach(([t,d],i)=>{
  const y=2.86+i*1.08; card(s,5.0,y,7.6,0.94);
  s.addShape(pres.ShapeType.ellipse,{x:5.28,y:y+0.35,w:0.22,h:0.22,fill:{color:NEG},line:{color:NEG,width:0}});
  s.addText(t,{x:5.66,y:y+0.14,w:6.7,h:0.32,fontSize:14,bold:true,color:INK,fontFace:B,isTextBox:true,margin:0});
  s.addText(d,{x:5.66,y:y+0.46,w:6.7,h:0.38,fontSize:12,color:MUT,fontFace:B,isTextBox:true,margin:0});
});
s.addText("그래서 두 가지를 시도했다 — ① USGS 값을 쓰는 방법을 고치기   ② 산사태 정답을 학습에 쓰기 (교수님 제안)",
  {x:0.7,y:5.3,w:11.9,h:0.4,fontSize:14.5,bold:true,color:ACC,fontFace:H,isTextBox:true,margin:0});
s.addNotes("출발점이 0.797, 그리고 피해 건수로 학습한 최종 결과가 0.722로 더 나빴다는 것이 문제의 시작이다.");

/* ─────────── 5 발견 ① 면적 항 ─────────── */
s=pres.addSlide(); s.background={color:WHT};
T(s,"발견 ① USGS 값을 잘못 쓰고 있었다","그 값은 “확률”이 아니라 “격자 한 칸에서 산사태가 덮는 면적 비율”이다");
s.addText("우리가 맞히려는 것은",{x:0.7,y:1.9,w:6.0,h:0.32,fontSize:13,color:MUT,fontFace:B,isTextBox:true,margin:0});
s.addText("“이 시정촌 어딘가에서 한 번이라도 났나”",{x:0.7,y:2.22,w:6.0,h:0.4,fontSize:18,bold:true,color:INK,fontFace:H,isTextBox:true,margin:0});
s.addText("그러면 시정촌이 넓을수록 칸이 많아지고,\n칸이 많으면 그중 하나라도 걸릴 가능성이 커진다.\n\n그런데 기존 식은 칸 수를 전혀 보지 않았다.",
  {x:0.7,y:2.78,w:6.0,h:1.4,fontSize:14,color:INK,lineSpacing:22,fontFace:B,isTextBox:true,margin:0});
s.addShape(pres.ShapeType.roundRect,{x:0.7,y:4.3,w:6.0,h:1.0,rectRadius:0.1,fill:{color:SOFT},line:{color:ACC,width:1.5}});
s.addText("고친 식",{x:1.0,y:4.44,w:5.4,h:0.28,fontSize:12,bold:true,color:ACC,fontFace:B,isTextBox:true,margin:0});
s.addText("USGS 값  ×  칸 수",{x:1.0,y:4.72,w:5.4,h:0.42,fontSize:20,bold:true,color:INK,fontFace:H,isTextBox:true,margin:0});
// 격자 그림
// 두 격자의 아래쪽을 같은 높이에 맞춰 라벨이 나란히 놓이게 한다
const grid=(x0,bottom,n,cell,on,lab,sub)=>{
  const y0 = bottom - n*cell;
  for(let r=0;r<n;r++) for(let c=0;c<n;c++){
    const hit = on.some(([rr,cc])=>rr===r&&cc===c);
    s.addShape(pres.ShapeType.rect,{x:x0+c*cell,y:y0+r*cell,w:cell-0.02,h:cell-0.02,
      fill:{color:hit?ACC:"F4F7F8"},line:{color:hit?ACC:LINE,width:0.5}});
  }
  s.addText(lab,{x:x0-0.45,y:bottom+0.1,w:n*cell+0.9,h:0.28,fontSize:12.5,bold:true,color:INK,align:"center",fontFace:B,isTextBox:true,margin:0});
  s.addText(sub,{x:x0-0.45,y:bottom+0.38,w:n*cell+0.9,h:0.28,fontSize:10.5,color:MUT,align:"center",fontFace:B,isTextBox:true,margin:0});
};
s.addText("같은 USGS 값(약 11%)이어도",{x:7.1,y:1.9,w:5.5,h:0.32,fontSize:13,color:MUT,fontFace:B,isTextBox:true,margin:0});
grid(7.7,4.12,3,0.30,[[1,1]],"좁은 시정촌","칸 9개 → 기대 1칸");
grid(9.8,4.12,6,0.30,[[0,2],[2,1],[3,4],[5,3]],"넓은 시정촌","칸 36개 → 기대 4칸");
s.addText("넓은 쪽이 “어딘가에서 한 번이라도” 날 가능성이 훨씬 크다",
  {x:7.1,y:4.9,w:5.5,h:0.56,fontSize:13,bold:true,color:ACC,align:"center",lineSpacing:18,fontFace:B,isTextBox:true,margin:0});
s.addText("실제 칸 수는 시정촌당 4,000 ~ 30,000개다 (구마모토시 8,661 · 아쓰마초 10,330). 그림은 개념만 나타낸 것이다.",
  {x:0.7,y:5.62,w:11.9,h:0.32,fontSize:11,color:MUT,italic:true,fontFace:B,isTextBox:true,margin:0});
s.addNotes("k = 시정촌 면적 ÷ 격자 한 칸 넓이. 칸이 독립이면 기대 칸 수 = USGS 값 × k 이고, 로그를 취하면 두 항의 합이 된다.");

/* ─────────── 6 발견 ① 결과 ─────────── */
s=pres.addSlide(); s.background={color:WHT};
T(s,"칸 수를 곱하자 바로 올랐다","학습을 하나도 안 했다. 엑셀에 이미 있던 열 두 개를 곱한 것뿐이다");
stat(s,0.9,2.05,2.85,"0.797","USGS 값만",MUT,"기존");
arrow(s,3.95,2.6);
stat(s,4.95,2.05,2.85,"0.840","× 칸 수",ACC,"학습 없음");
arrow(s,8.0,2.6);
stat(s,9.0,2.05,2.85,"0.855","최종 모델",POS,"여기까지가 전부");
s.addShape(pres.ShapeType.roundRect,{x:0.9,y:4.12,w:11.0,h:1.05,rectRadius:0.1,fill:{color:SURF},line:{color:LINE,width:0.5}});
s.addText("참고로 — 칸 수(시정촌 면적)만으로도 0.821이 나온다. USGS 값 단독(0.797)보다 높다.",
  {x:1.2,y:4.28,w:10.4,h:0.34,fontSize:14,bold:true,color:INK,fontFace:H,isTextBox:true,margin:0});
s.addText("그렇다고 “넓으면 라벨이 켜지는 것”은 아니다. 액상화에서는 면적만으로는 0.547(거의 찍기)인데도 USGS 값과 곱하면 0.715 → 0.770으로 오른다.",
  {x:1.2,y:4.66,w:10.4,h:0.38,fontSize:12.5,color:MUT,fontFace:B,isTextBox:true,margin:0});
s.addText("여기서 “최종 모델”은 이 사전확률을 기존 회귀·우도에 통과시킨 결과다. 뒤에서 그게 얼마나 기여했는지 따로 본다.",
  {x:0.9,y:5.42,w:11.0,h:0.34,fontSize:11.5,color:MUT,italic:true,fontFace:B,isTextBox:true,margin:0});
s.addNotes("0.855는 새로 얻은 값이 아니라 26.09.16 자료의 0.855를 재현한 것이다. 이번 실험에서 이 값을 넘은 조건은 없었다.");

/* ─────────── 7 교수님 제안 ─────────── */
s=pres.addSlide(); s.background={color:WHT};
T(s,"교수님 제안 — 산사태 정답을 학습에도 쓰자","단, 그러면 “정답을 보고 맞힌 것”이 되니 지진을 하나씩 가려서 시험한다");
const EV=["돗토리","니가타","구마모토","오사카","훗카이도"];
EV.forEach((e,i)=>s.addText(e,{x:2.55+i*1.92,y:2.0,w:1.8,h:0.3,fontSize:13,bold:true,color:INK,align:"center",fontFace:B,isTextBox:true,margin:0}));
for(let r=0;r<5;r++){
  s.addText(`${r+1}회차`,{x:0.95,y:2.44+r*0.62,w:1.4,h:0.5,fontSize:13,bold:true,color:MUT,valign:"middle",fontFace:B,isTextBox:true,margin:0});
  for(let c=0;c<5;c++){
    const test = r===c;
    s.addShape(pres.ShapeType.roundRect,{x:2.55+c*1.92,y:2.44+r*0.62,w:1.8,h:0.5,rectRadius:0.06,
      fill:{color:test?NEG:SOFT},line:{color:test?NEG:LINE,width:test?1.25:0.5}});
    s.addText(test?"시험":"학습",{x:2.55+c*1.92,y:2.44+r*0.62,w:1.8,h:0.5,fontSize:12,bold:true,
      color:test?WHT:ACC,align:"center",valign:"middle",fontFace:B,isTextBox:true,margin:0});
  }
}
s.addText("한 회차에서 지진 하나를 빼놓고 나머지 넷의 정답으로 배운 다음, 빼놓은 지진에서 점수를 낸다. 이걸 다섯 번 돌린다.",
  {x:0.95,y:5.74,w:11.5,h:0.36,fontSize:14,bold:true,color:INK,fontFace:H,isTextBox:true,margin:0});
s.addText("가리는 것은 그 지진의 산사태 정답뿐이다. 피해 건수는 그대로 쓴다. 회차마다 모델을 처음부터 새로 만든다.",
  {x:0.95,y:6.14,w:11.5,h:0.34,fontSize:12.5,color:MUT,fontFace:B,isTextBox:true,margin:0});
s.addNotes("이것이 LOEO(Leave-One-Event-Out)다. 정답을 학습에 쓰면서도 성능을 정직하게 잴 수 있다.");

/* ─────────── 8 발견 ② 제안은 작동 ─────────── */
s=pres.addSlide(); s.background={color:WHT};
T(s,"발견 ② 제안은 작동했다 — 칸 수를 안 곱했을 때","기존 방식 위에 정답 학습을 얹으니 크게 올랐다");
card(s,0.9,1.95,11.0,2.0,"EDF3EF",POS);
s.addText("기존 방식 (칸 수 없음)",{x:1.25,y:2.16,w:4.5,h:0.32,fontSize:13,bold:true,color:POS,fontFace:B,isTextBox:true,margin:0});
s.addText("0.722",{x:1.25,y:2.52,w:2.3,h:0.72,fontSize:40,bold:true,color:MUT,fontFace:H,isTextBox:true,margin:0});
s.addText("정답 학습 안 함",{x:1.25,y:3.26,w:2.3,h:0.3,fontSize:11.5,color:MUT,fontFace:B,isTextBox:true,margin:0});
arrow(s,3.8,2.62);
s.addText("0.804",{x:5.0,y:2.52,w:2.3,h:0.72,fontSize:40,bold:true,color:POS,fontFace:H,isTextBox:true,margin:0});
s.addText("정답 학습 함",{x:5.0,y:3.26,w:2.3,h:0.3,fontSize:11.5,color:POS,bold:true,fontFace:B,isTextBox:true,margin:0});
s.addText("＋0.082",{x:7.9,y:2.4,w:3.7,h:0.5,fontSize:26,bold:true,color:POS,fontFace:H,isTextBox:true,margin:0});
s.addText("우연일 확률 2% 미만\n다섯 회차 모두 같은 방향으로 학습됐다",
  {x:7.9,y:2.94,w:3.7,h:0.62,fontSize:12,color:MUT,lineSpacing:16,fontFace:B,isTextBox:true,margin:0});
s.addText("무엇이 달라졌나",{x:0.9,y:4.24,w:11.0,h:0.34,fontSize:14.5,bold:true,color:INK,fontFace:H,isTextBox:true,margin:0});
[["정답을 안 주면 모델이 산지 비율을 거의 무시한다","산지의 영향력을 나타내는 값이 0.05 수준으로 남는다 — 사실상 안 배운 것이다"],
 ["정답을 주면 제대로 배운다","같은 값이 0.93 ~ 1.37로 커지고, 다섯 회차 모두 “산이 많으면 산사태가 많다”는 올바른 방향이었다"]]
 .forEach(([t,d],i)=>{
  const y=4.64+i*0.82; card(s,0.9,y,11.0,0.72);
  s.addShape(pres.ShapeType.ellipse,{x:1.18,y:y+0.26,w:0.2,h:0.2,fill:{color:POS},line:{color:POS,width:0}});
  s.addText(t,{x:1.54,y:y+0.06,w:10.0,h:0.3,fontSize:13.5,bold:true,color:INK,fontFace:B,isTextBox:true,margin:0});
  s.addText(d,{x:1.54,y:y+0.36,w:10.0,h:0.3,fontSize:11.5,color:MUT,fontFace:B,isTextBox:true,margin:0});
});
s.addNotes("교수님 제안은 방법으로서 검증됐다. 0.722 → 0.804, P(개선>0)=0.98, 5회차 κ 전부 양수.");

/* ─────────── 9 발견 ② 그런데 ─────────── */
s=pres.addSlide(); s.background={color:WHT};
T(s,"그런데 칸 수를 곱한 뒤에는 오르지 않았다","같은 정답 학습을 얹었는데 이번에는 제자리였다");
card(s,0.9,1.95,11.0,1.9,"F7EDEA",NEG);
s.addText("칸 수를 곱한 방식",{x:1.25,y:2.14,w:4.5,h:0.32,fontSize:13,bold:true,color:NEG,fontFace:B,isTextBox:true,margin:0});
s.addText("0.855",{x:1.25,y:2.48,w:2.3,h:0.72,fontSize:40,bold:true,color:POS,fontFace:H,isTextBox:true,margin:0});
s.addText("정답 학습 안 함",{x:1.25,y:3.22,w:2.3,h:0.3,fontSize:11.5,color:MUT,fontFace:B,isTextBox:true,margin:0});
arrow(s,3.8,2.58);
s.addText("0.851",{x:5.0,y:2.48,w:2.3,h:0.72,fontSize:40,bold:true,color:NEG,fontFace:H,isTextBox:true,margin:0});
s.addText("정답 학습 함",{x:5.0,y:3.22,w:2.3,h:0.3,fontSize:11.5,color:NEG,bold:true,fontFace:B,isTextBox:true,margin:0});
s.addText("－0.004",{x:7.9,y:2.38,w:3.7,h:0.5,fontSize:26,bold:true,color:NEG,fontFace:H,isTextBox:true,margin:0});
s.addText("오히려 살짝 내려갔다\n다시 뽑은 3,000개 표본 전부에서 못 넘었다",
  {x:7.9,y:2.9,w:3.7,h:0.62,fontSize:12,color:MUT,lineSpacing:16,fontFace:B,isTextBox:true,margin:0});
s.addShape(pres.ShapeType.roundRect,{x:0.9,y:4.16,w:11.0,h:1.02,rectRadius:0.1,fill:{color:DARK},line:{color:DARK,width:0}});
s.addText("더 이상한 것 — 정답 없이 산지 비율만 얹으면 크게 망가진다",
  {x:1.2,y:4.3,w:10.4,h:0.34,fontSize:14.5,bold:true,color:NEG_L,fontFace:H,isTextBox:true,margin:0});
s.addText("0.855  →  0.729. 산지 비율을 넣되 정답으로 잡아주지 않으면 모델이 엉뚱한 방향으로 배운다. 정답 학습은 그 폭주를 막아 0.851로 되돌리는 일을 한 것이다.",
  {x:1.2,y:4.66,w:10.4,h:0.4,fontSize:12.5,color:"C3CFD6",fontFace:B,isTextBox:true,margin:0});
s.addText("즉 정답 학습은 분명히 일을 한다. 다만 “자기가 만든 손해를 메우는 일”이어서, 애초에 산지 비율을 안 넣은 쪽이 가장 좋았다.",
  {x:0.9,y:5.42,w:11.0,h:0.38,fontSize:14,bold:true,color:INK,fontFace:H,isTextBox:true,margin:0});
s.addNotes("B1 0.7285 → B2 0.8507 이 +0.122로 P=1.0이다. 감독은 확실히 일을 한다. 그래도 B0 0.8550을 못 넘는다.");

/* ─────────── 10 왜 ─────────── */
s=pres.addSlide(); s.background={color:WHT};
T(s,"왜 더 오르지 않았나","칸 수와 산지 비율이 사실 같은 것을 재고 있었다");
s.addShape(pres.ShapeType.ellipse,{x:2.3,y:2.0,w:3.3,h:3.3,fill:{color:ACC,transparency:62},line:{color:ACC,width:1.5}});
s.addShape(pres.ShapeType.ellipse,{x:4.3,y:2.0,w:3.3,h:3.3,fill:{color:POS,transparency:62},line:{color:POS,width:1.5}});
s.addText("칸 수\n(시정촌 면적)",{x:1.95,y:3.2,w:1.9,h:0.8,fontSize:13,bold:true,color:ACC,align:"center",lineSpacing:18,fontFace:B,isTextBox:true,margin:0});
s.addText("산지 비율",{x:6.0,y:3.45,w:1.6,h:0.36,fontSize:13,bold:true,color:POS,align:"center",fontFace:B,isTextBox:true,margin:0});
s.addText("겹침\n0.53",{x:4.55,y:3.2,w:0.8,h:0.8,fontSize:15,bold:true,color:INK,align:"center",lineSpacing:19,fontFace:H,isTextBox:true,margin:0});
s.addText("산이 많은 곳은 대체로 넓은 시정촌이다",{x:1.9,y:5.42,w:6.1,h:0.36,fontSize:13.5,bold:true,color:INK,align:"center",fontFace:B,isTextBox:true,margin:0});
card(s,8.4,2.0,4.2,3.3);
s.addText("숫자로도 보인다",{x:8.7,y:2.22,w:3.6,h:0.32,fontSize:13,bold:true,color:ACC,fontFace:B,isTextBox:true,margin:0});
s.addText("정답을 학습해서 도달한 점수",{x:8.7,y:2.66,w:3.6,h:0.3,fontSize:12,color:MUT,fontFace:B,isTextBox:true,margin:0});
s.addText("0.834",{x:8.7,y:2.96,w:3.6,h:0.56,fontSize:30,bold:true,color:POS,fontFace:H,isTextBox:true,margin:0});
s.addText("칸 수를 곱해서 얻은 점수",{x:8.7,y:3.66,w:3.6,h:0.3,fontSize:12,color:MUT,fontFace:B,isTextBox:true,margin:0});
s.addText("0.840",{x:8.7,y:3.96,w:3.6,h:0.56,fontSize:30,bold:true,color:ACC,fontFace:H,isTextBox:true,margin:0});
s.addText("거의 같은 자리에 도착했다.\n서로 다른 길로 같은 정보에 닿은 것이다.",
  {x:8.7,y:4.66,w:3.6,h:0.6,fontSize:12,bold:true,color:INK,lineSpacing:17,fontFace:B,isTextBox:true,margin:0});
s.addText("이미 아는 것을 다시 가르칠 수는 없다 — 그래서 칸 수를 곱한 뒤에는 산지 비율이 더 보탤 것이 없었다.",
  {x:0.7,y:5.94,w:11.9,h:0.38,fontSize:14,bold:true,color:ACC,fontFace:H,isTextBox:true,margin:0});
s.addNotes("corr(log k, 산지 비율) = 0.53. A2가 정답으로 배워 도달한 사전 0.8341이 면적 항이 구조만으로 얻은 0.8400과 같은 자리다.");

/* ─────────── 11 발견 ③ ─────────── */
s=pres.addSlide(); s.background={color:WHT};
T(s,"발견 ③ 학습한 모델이 거의 기여하지 않는다","엑셀 두 열을 곱한 점수와, 3000번 학습한 최종 점수를 비교해 보면");
s.addText("음성(산사태 없음) 사례가 넉넉한 세 지진만 떼어놓고 보면",{x:0.9,y:1.98,w:11.0,h:0.34,fontSize:14,bold:true,color:INK,fontFace:H,isTextBox:true,margin:0});
stat(s,1.6,2.48,3.3,"0.8177","곱하기만 한 점수",ACC,"학습 없음");
s.addText("=",{x:5.2,y:3.0,w:0.8,h:0.6,fontSize:38,bold:true,color:MUT,align:"center",valign:"middle",fontFace:H,isTextBox:true,margin:0});
stat(s,6.3,2.48,3.3,"0.8177","학습한 최종 점수",MUT,"3000번 학습");
s.addText("차이\n0.0000",{x:10.1,y:2.76,w:2.2,h:0.9,fontSize:20,bold:true,color:NEG,align:"center",lineSpacing:26,fontFace:H,isTextBox:true,margin:0});
s.addShape(pres.ShapeType.roundRect,{x:0.9,y:4.5,w:11.0,h:1.5,rectRadius:0.1,fill:{color:SURF},line:{color:LINE,width:0.5}});
s.addText("전체로 보면 0.840 → 0.855로 조금 오르는데, 그 차이가 어디서 오는지 뜯어보니",
  {x:1.2,y:4.66,w:10.4,h:0.34,fontSize:13.5,bold:true,color:INK,fontFace:H,isTextBox:true,margin:0});
s.addText("다섯 지진 중 넷은 곱하기만 한 점수와 학습한 점수가 완전히 같았다. 오른 것은 음성이 2개뿐인 지진 하나에서였다.\n즉 지금 산사태 순서는 사실상 엑셀 두 열이 다 만들고 있다. 회귀 모델이 보태는 것은 측정되지 않는다.",
  {x:1.2,y:5.04,w:10.4,h:0.78,fontSize:13,color:MUT,lineSpacing:19,fontFace:B,isTextBox:true,margin:0});
s.addText("기존 방식에서는 더 나쁘다 — 곱하기 전 점수 0.797을 학습이 0.722로 깎아먹었다.",
  {x:0.9,y:6.14,w:11.0,h:0.36,fontSize:13.5,bold:true,color:NEG,fontFace:B,isTextBox:true,margin:0});
s.addNotes("B0은 음성이 3개 이상인 세 지진(돗토리·구마모토·훗카이도, 가중치 66)에서 사전 = 사후 = 0.8177이다. 전체 83행의 +0.015는 2004 니가타(16쌍) 한 곳에서 나온다.");

/* ─────────── 12 결론 ─────────── */
s=pres.addSlide(); s.background={color:DARK};
s.addText("그래서 무엇을 쓰면 되나",{x:0.9,y:0.62,w:11.6,h:0.62,fontSize:31,bold:true,color:WHT,fontFace:H,isTextBox:true,margin:0});
s.addText("가장 좋았던 것은 가장 단순한 것이었다",{x:0.9,y:1.28,w:11.6,h:0.36,fontSize:14,color:"9AA9B2",fontFace:B,isTextBox:true,margin:0});
s.addShape(pres.ShapeType.roundRect,{x:0.9,y:1.96,w:11.6,h:1.5,rectRadius:0.1,fill:{color:DARK2},line:{color:ACC_L,width:1.5}});
s.addText("USGS 값  ×  칸 수",{x:1.3,y:2.16,w:6.0,h:0.6,fontSize:28,bold:true,color:WHT,fontFace:H,isTextBox:true,margin:0});
s.addText("산지 비율을 넣지 않고, 산사태 정답도 쓰지 않고, 사전확률에 학습할 값이 하나도 없다.",
  {x:1.3,y:2.82,w:10.8,h:0.36,fontSize:13.5,color:"C3CFD6",fontFace:B,isTextBox:true,margin:0});
[["0.855","산사태 점수"],["0.781","액상화 점수"],["0개","학습할 값"],["안 씀","산사태 정답"]].forEach(([v,l],i)=>{
  const x=0.9+i*2.95;
  s.addShape(pres.ShapeType.roundRect,{x,y:3.74,w:2.75,h:1.35,rectRadius:0.1,fill:{color:DARK2},line:{color:"31424F",width:0.75}});
  s.addText(v,{x:x+0.1,y:3.92,w:2.55,h:0.6,fontSize:28,bold:true,color:i<2?ACC_L:WHT,align:"center",fontFace:H,isTextBox:true,margin:0});
  s.addText(l,{x:x+0.1,y:4.56,w:2.55,h:0.32,fontSize:12,color:"9AA9B2",align:"center",fontFace:B,isTextBox:true,margin:0});
});
s.addText("교수님 제안은 어떻게 보고할까",{x:0.9,y:5.42,w:11.6,h:0.34,fontSize:14,bold:true,color:ACC_L,fontFace:H,isTextBox:true,margin:0});
s.addText("“제안하신 절차는 기존 방식 위에서 유의하게 작동했습니다(0.722 → 0.804). 다만 칸 수를 곱하는 수정이 이미 같은 정보를 담고 있어\n그 위에서는 추가 이득이 없었습니다. 감독 구조는 유지하고, 칸 수가 모르는 변수로 바꿔볼 차례입니다.”",
  {x:0.9,y:5.78,w:11.6,h:0.8,fontSize:13,color:"C3CFD6",lineSpacing:19,fontFace:B,isTextBox:true,margin:0});
s.addNotes("가장 좋은 결과가 가장 적게 학습한 구성이라는 것이 핵심 메시지다.");

/* ─────────── 13 한계 ─────────── */
s=pres.addSlide(); s.background={color:WHT};
T(s,"솔직하게 말해둘 것","숫자를 어디까지 믿을 수 있는지부터");
[["“산사태 없음” 사례가 20개뿐이다","점수를 만드는 비교 쌍이 전부 합쳐 275개다. 어떤 지진은 음성이 2개뿐이라 그 지진 점수는 거의 우연에 가깝다. 모든 산사태 숫자에 이 한계가 걸린다.",NEG],
 ["0.855는 새로 얻은 값이 아니다","이미 갖고 있던 자료의 0.855와 같다. 이번 실험에서 그 값을 넘은 조건은 없었다. 새로 밝혀진 것은 왜 넘지 못하는가다.",NEG],
 ["훗카이도 지진의 라벨을 다시 봐야 한다","산이 많은 히다카초·유바리시가 “산사태 없음”이고, 평지인 기타히로시마시가 “있음”이다. 자료상 없음인지 조사 항목이 없어서 없음인지 확인이 필요하다.",NEG],
 ["액상화는 확률값이 크게 어긋나 있다","순서는 잘 맞히는데(0.770), 모델이 “거의 다 액상화 난다(91%)”고 말한다. 실제는 절반 이하다. 별도로 고칠 부분이다.",NEG]]
 .forEach(([t,d,c],i)=>{
  const y=1.9+i*1.2; card(s,0.9,y,11.6,1.02);
  s.addShape(pres.ShapeType.ellipse,{x:1.2,y:y+0.38,w:0.24,h:0.24,fill:{color:c},line:{color:c,width:0}});
  s.addText(t,{x:1.62,y:y+0.14,w:10.6,h:0.32,fontSize:14,bold:true,color:INK,fontFace:B,isTextBox:true,margin:0});
  s.addText(d,{x:1.62,y:y+0.46,w:10.6,h:0.44,fontSize:12,color:MUT,fontFace:B,isTextBox:true,margin:0});
});
s.addNotes("한계를 먼저 말하는 것이 신뢰를 만든다. 특히 음성 20개라는 제약은 모든 LS 숫자에 걸린다.");

/* ─────────── 14 다음 ─────────── */
s=pres.addSlide(); s.background={color:WHT};
T(s,"다음에 해볼 것","이번 결과가 가리키는 방향");
[["감독 대상을 산지 비율이 아닌 것으로 바꾼다","칸 수가 아직 모르는 정보 — 경사도, 지질, 강우 — 로 바꾸면 기존 방식에서 본 +0.082가 살아날 수 있다."],
 ["회귀 모델 쪽을 들여다본다","지금 산사태 순서에 거의 기여하지 못하고 있다. 어느 피해 항목이 순서를 흐리는지 하나씩 끄고 다시 재본다."],
 ["액상화 확률값을 바로잡는다","값 하나를 풀어주니 액상화 점수가 0.781 → 0.816으로 올랐다. 정식 조건으로 다시 확인할 차례다."],
 ["훗카이도 라벨을 원자료에서 확인한다","산지 비율이 거꾸로 작동하는 유일한 지진이고, 이 지진 하나가 결과를 흔들었다."]]
 .forEach(([t,d],i)=>{
  const y=1.9+i*1.2; card(s,0.9,y,11.6,1.02);
  s.addShape(pres.ShapeType.ellipse,{x:1.18,y:y+0.31,w:0.4,h:0.4,fill:{color:ACC},line:{color:ACC,width:0}});
  s.addText(String(i+1),{x:1.18,y:y+0.31,w:0.4,h:0.4,fontSize:14,bold:true,color:WHT,align:"center",valign:"middle",fontFace:H,isTextBox:true,margin:0});
  s.addText(t,{x:1.76,y:y+0.14,w:10.5,h:0.32,fontSize:14,bold:true,color:INK,fontFace:B,isTextBox:true,margin:0});
  s.addText(d,{x:1.76,y:y+0.46,w:10.5,h:0.44,fontSize:12,color:MUT,fontFace:B,isTextBox:true,margin:0});
});
s.addText("조건별 상세 설정과 전체 숫자는 별도 자료에 있다 — LOEO_발표자료_상세.pptx (16장) · LOEO_결과.xlsx (7시트)",
  {x:0.9,y:6.62,w:11.6,h:0.32,fontSize:11,color:MUT,italic:true,fontFace:B,isTextBox:true,margin:0});
s.addNotes("이 쉬운 버전은 이해를 위한 것이고, 질문에 답할 때 필요한 상세 표는 별도 자료에 있다.");

pres.writeFile({fileName: process.argv[2]}).then(f=>console.log("작성:",f));
