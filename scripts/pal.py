import numpy as np
def srgb2lab(h):
    c=np.array([int(h[i:i+2],16) for i in (1,3,5)])/255.0
    c=np.where(c<=0.04045,c/12.92,((c+0.055)/1.055)**2.4)
    M=np.array([[0.4124,0.3576,0.1805],[0.2126,0.7152,0.0722],[0.0193,0.1192,0.9505]])
    xyz=M@c/np.array([0.95047,1.0,1.08883])
    f=np.where(xyz>0.008856,np.cbrt(xyz),7.787*xyz+16/116)
    return np.array([116*f[1]-16,500*(f[0]-f[1]),200*(f[1]-f[2])])
def lch2hex(L,C,h):
    a=C*np.cos(np.radians(h)); b=C*np.sin(np.radians(h))
    fy=(L+16)/116; fx=fy+a/500; fz=fy-b/200
    f=np.array([fx,fy,fz]); xyz=np.where(f**3>0.008856,f**3,(f-16/116)/7.787)*np.array([0.95047,1.0,1.08883])
    M=np.linalg.inv(np.array([[0.4124,0.3576,0.1805],[0.2126,0.7152,0.0722],[0.0193,0.1192,0.9505]]))
    rgb=M@xyz
    if (rgb<-0.001).any() or (rgb>1.001).any(): return None
    rgb=np.clip(rgb,0,1); rgb=np.where(rgb<=0.0031308,12.92*rgb,1.055*rgb**(1/2.4)-0.055)
    return '#%02X%02X%02X'%tuple(int(round(v*255)) for v in rgb)
ab=['#00897B','#80CBC4','#1E5BD8','#9DB8F2','#7B1FA2','#CE93D8','#D81B60','#F48FB1','#EF6C00','#FFCC80','#558B2F','#C5E1A5','#F2B700','#FFE082','#6D4C41','#BCAAA4','#C62828','#EF9A9A','#00A5CF','#A5E3F3']
other=['#E9A094','#FFFFFF']   # epitope tint, background
avoid=np.array([srgb2lab(h) for h in ab+other])
rng=np.random.default_rng(3)
best=(0,None)
for it in range(60000):
    cols=[];labs=[]
    for k in range(6):
        for _ in range(20):
            L=rng.uniform(42,66); C=rng.uniform(16,42); h=rng.uniform(0,360)
            hx=lch2hex(L,C,h)
            if hx: break
        else: break
        cols.append(hx); labs.append(srgb2lab(hx))
    if len(cols)<6: continue
    labs=np.array(labs)
    d_ab=np.min(np.linalg.norm(labs[:,None]-avoid[None],axis=2))
    pw=np.linalg.norm(labs[:,None]-labs[None],axis=2)+np.eye(6)*1e3
    sc=min(d_ab,pw.min()*1.1)
    if sc>best[0]: best=(sc,cols,d_ab,pw.min())
print(best)
