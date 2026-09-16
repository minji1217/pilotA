"""렌더링 없이 하는 기하 QA. 슬라이드 경계 이탈, 겹침, 대략적인 텍스트 넘침을 잡는다."""
import zipfile, re, sys
from defusedxml import minidom

EMU=914400.0; W,H=13.333,7.5; MARGIN=0.4
Z=zipfile.ZipFile(sys.argv[1])
names=sorted([n for n in Z.namelist() if re.fullmatch(r"ppt/slides/slide\d+\.xml",n)],
             key=lambda n:int(re.search(r"\d+",n.split("/")[-1]).group()))
issues=[]
for si,n in enumerate(names,1):
    doc=minidom.parseString(Z.read(n))
    boxes=[]
    for sp in doc.getElementsByTagName("p:sp")+doc.getElementsByTagName("p:graphicFrame"):
        off=sp.getElementsByTagName("a:off"); ext=sp.getElementsByTagName("a:ext")
        if not off or not ext: continue
        x=int(off[0].getAttribute("x"))/EMU; y=int(off[0].getAttribute("y"))/EMU
        w=int(ext[0].getAttribute("cx"))/EMU; h=int(ext[0].getAttribute("cy"))/EMU
        txt="".join(t.firstChild.nodeValue for t in sp.getElementsByTagName("a:t") if t.firstChild)
        sizes=[int(r.getAttribute("sz"))/100 for r in sp.getElementsByTagName("a:rPr") if r.getAttribute("sz")]
        sz=max(sizes) if sizes else 18
        isTx=bool(sp.getElementsByTagName("a:txBox")) or bool(txt)
        boxes.append((x,y,w,h,txt,sz,isTx))
        if x < -0.01 or y < -0.01 or x+w > W+0.01 or y+h > H+0.01:
            issues.append(f"S{si}: 슬라이드 밖  x={x:.2f} y={y:.2f} w={w:.2f} h={h:.2f}  «{txt[:28]}»")
        elif txt and (x < MARGIN-0.01 or y < MARGIN-0.01 or x+w > W-MARGIN+0.01 or y+h > H-MARGIN+0.01):
            issues.append(f"S{si}: 여백 {MARGIN}\" 부족  x={x:.2f} y={y:.2f} 우={x+w:.2f} 하={y+h:.2f}  «{txt[:28]}»")
        # 대략적인 텍스트 넘침: 글자당 폭 ≈ 0.52*pt (한글은 넓게 잡음)
        if txt and h>0 and w>0:
            cpl=max(1,int(w/(sz/72*0.62)))
            lines=sum(max(1,(len(seg)+cpl-1)//cpl) for seg in txt.split("\n"))
            need=lines*(sz/72*1.32)
            if need > h*1.18:
                issues.append(f"S{si}: 텍스트 넘침 가능  필요≈{need:.2f}\" > 상자 {h:.2f}\"  {sz:.0f}pt  «{txt[:34]}»")
    # 텍스트 상자끼리 겹침
    tb=[b for b in boxes if b[6] and b[4]]
    for i in range(len(tb)):
        for j in range(i+1,len(tb)):
            a,b=tb[i],tb[j]
            ox=min(a[0]+a[2],b[0]+b[2])-max(a[0],b[0])
            oy=min(a[1]+a[3],b[1]+b[3])-max(a[1],b[1])
            if ox>0.06 and oy>0.06:
                issues.append(f"S{si}: 텍스트 겹침 {ox:.2f}x{oy:.2f}\"  «{a[4][:20]}» ↔ «{b[4][:20]}»")
print(f"슬라이드 {len(names)}장 검사")
print("\n".join(issues) if issues else "문제 없음")
print(f"\n합계 {len(issues)}건")
