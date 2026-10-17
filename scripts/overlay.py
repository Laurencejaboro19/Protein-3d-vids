import sys, json, os
from PIL import Image, ImageDraw, ImageFont
W,H=1080,1350; FPS=20; T0=3.6; SLOT=1.32; NAB=10
iptm=json.load(open('iptm.json'))
F=lambda n,s: ImageFont.truetype(f'/usr/share/fonts/opentype/inter/{n}.otf',s)
fHead,fTitle,fSub,fLab,fBig,fSmall,fFoot=F('Inter-Bold',27),F('Inter-Bold',80),F('Inter-Medium',27),F('Inter-Medium',32),F('Inter-Bold',92),F('Inter-Medium',27),F('Inter-Medium',20)
NAVY='#12294F'; GREY='#7A869A'; TEAL='#1FB5A8'
ab={1:'#00897B',2:'#1E5BD8',3:'#7B1FA2',4:'#D81B60',5:'#EF6C00',6:'#558B2F',7:'#C99700',8:'#6D4C41',9:'#C62828',10:'#0090B5'}
def tracked(d,xy,txt,font,fill,sp=4.5):
    x,y=xy
    for ch in txt:
        d.text((x,y),ch,font=font,fill=fill); x+=d.textlength(ch,font=font)+sp
def draw(f,src=None):
    t=f/FPS
    im=Image.open(src or f'frames/f{f:04d}.png').convert('RGB'); d=ImageDraw.Draw(im)
    d.rectangle((0,0,W,222),fill='white'); d.rectangle((0,1120,W,H),fill='white')
    tracked(d,(60,44),"PDFA × MINISTRY OF HEALTH",fHead,GREY)
    d.text((58,84),"Lassa fever antibodies",font=fTitle,fill=NAVY)
    sub="Target: Lassa virus glycoprotein trimer (PDB 8EJE)" if t<T0 else "30,000+ de novo antibodies designed · 10 shown, docked on the same site"
    d.text((60,182),sub,font=fSub,fill=GREY)
    j=int((t-T0)//SLOT) if t>=T0 else -1
    if j<0:
        d.text((60,1196),"30,000+",font=fBig,fill=NAVY); w=d.textlength("30,000+",font=fBig)
        d.text((60+w+20,1236),"de novo antibodies",font=fLab,fill=NAVY)
        d.text((60,1160),"designed for the Lassa virus glycoprotein (GP1/GP2)",font=fSmall,fill=GREY)
    else:
        k=j%NAB+1; name=f"lasv_{k}"
        d.text((60,1236),"Antibody",font=fLab,fill=NAVY); x=60+d.textlength("Antibody ",font=fLab)
        d.text((x,1190),name,font=fBig,fill=ab[k]); x+=d.textlength(name+" ",font=fBig)
        d.text((x,1236),"of 30,000+ designs",font=fLab,fill=NAVY)
        d.text((60,1160),f"ipTM {iptm[str(k)]:.2f}  (VH–VL interface)",font=fSmall,fill=GREY)
    d.text((60,1300),"Computational models · antibody poses docked on the GP1/GP2 epitope · not experimental structures",font=fFoot,fill='#97A0B0')
    d.rectangle((0,H-8,int(W*min(t/30,1)),H),fill=TEAL)
    return im
if __name__=='__main__':
    for f in range(int(sys.argv[1]),int(sys.argv[2])):
        if os.path.exists(f'frames/f{f:04d}.png'): draw(f).save(f'out/f{f:04d}.png')
