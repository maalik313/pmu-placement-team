import sys
from pptx import Presentation
from pptx.util import Emu
from PIL import Image, ImageDraw, ImageFont
P=Presentation(sys.argv[1]); out=sys.argv[2]; SC=96/914400*1.0  # px per EMU -> 96dpi
R='/usr/share/fonts/truetype/liberation/LiberationSans-%s.ttf'
def font(sz,b): return ImageFont.truetype(R%('Bold' if b else 'Regular'), int(sz*96/72))
def wrap(d,t,f,w):
    lines=[];cur=''
    for word in t.split(' '):
        tt=(cur+' '+word).strip()
        if d.textlength(tt,font=f)<=w or not cur: cur=tt
        else: lines.append(cur);cur=word
    lines.append(cur);return lines
for n,s in enumerate(P.slides):
    im=Image.new('RGB',(1280,720),'white'); d=ImageDraw.Draw(im); warn=[]
    for sh in s.shapes:
        x,y,w,h=[v*SC for v in (sh.left,sh.top,sh.width,sh.height)]
        if sh.shape_type==13 or sh.shape_type==16:
            try:
                src=Image.open(sh.image.blob if hasattr(sh,'image') else None) if False else None
            except: pass
            try:
                import io; pi=Image.open(io.BytesIO(sh.image.blob)).convert('RGB').resize((int(w),int(h))); im.paste(pi,(int(x),int(y)))
            except Exception: d.rectangle([x,y,x+w,y+h],outline='gray')
            continue
        if sh.shape_type==1:
            try:
                f=sh.fill; col='#'+str(f.fore_color.rgb) if f.type==1 else None
            except Exception: col=None
            if col and 'alpha' not in sh._element.xml: 
                (d.ellipse if 'ellipse' in sh._element.xml else d.rectangle)([x,y,x+w,y+h],fill=col)
            try:
                if sh.line.fill.type==1: d.rounded_rectangle([x,y,x+w,y+h],8,outline='#'+str(sh.line.color.rgb),width=2)
            except Exception: pass
        if sh.has_text_frame and sh.text_frame.text.strip():
            ty=y; 
            for p in sh.text_frame.paragraphs:
                if not p.runs: continue
                r=p.runs[0]; f=font(r.font.size.pt,bool(r.font.bold)); c='#'+str(r.font.color.rgb)
                sp=(p.space_before.pt*96/72) if p.space_before else 0; ty+=sp
                for ln in wrap(d,''.join(r.text for r in p.runs),f,w):
                    tw=d.textlength(ln,font=f); tx=x+(w-tw)/2 if p.alignment==2 else x
                    yy=ty+(h-f.size*1.2)/2 if sh.text_frame.vertical_anchor==3 and len(p.runs)==1 and ty==y else ty
                    d.text((tx,yy),ln,font=f,fill=c); ty+=f.size*1.2
            if ty>y+h+4 and sh.text_frame.vertical_anchor!=3: warn.append((sh.text_frame.text[:30],round(ty-(y+h))))
    im.save(f'{out}{n}.png'); print(n,'overflow:',warn)
