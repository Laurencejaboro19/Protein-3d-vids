import sys, numpy as np, pymol, time
from pymol import cmd
pymol.finish_launching(['pymol','-cq'])
W,H=1080,1350; FPS=20
f0,f1=int(sys.argv[1]),int(sys.argv[2]); SHADOW=int(sys.argv[3]) if len(sys.argv)>3 else 1
T0=3.6; SLOT=1.32; FADE=0.35; NAB=10
cmd.set('orthoscopic',1); cmd.bg_color('white'); cmd.set('ray_opaque_background',1)
cmd.set('antialias',1); cmd.set('ray_shadow',SHADOW); cmd.set('depth_cue',0)
cmd.set('ambient',0.42); cmd.set('specular',0.12); cmd.set('direct',0.5); cmd.set('ray_trace_mode',0)
cmd.set('hash_max',800); cmd.set('cartoon_sampling',5); cmd.set('cartoon_loop_quality',3); cmd.set('cartoon_oval_quality',4); cmd.set('cartoon_tube_quality',4)
cmd.set('cartoon_fancy_helices',1); cmd.set('cartoon_loop_radius',0.32); cmd.set('cartoon_oval_length',1.5); cmd.set('cartoon_rect_length',1.4)
cmd.set('ray_max_passes',1); cmd.set('two_sided_lighting',1); cmd.set('surface_quality',1); cmd.set('transparency_mode',2)
def hexc(name,h): cmd.set_color(name,[int(h[i:i+2],16)/255 for i in (1,3,5)])
hexc('tgrey','#C9CED4'); hexc('epi','#E9A094')
ab_col={1:('#00897B','#80CBC4'),2:('#1E5BD8','#9DB8F2'),3:('#7B1FA2','#CE93D8'),4:('#D81B60','#F48FB1'),5:('#EF6C00','#FFCC80'),6:('#558B2F','#C5E1A5'),7:('#F2B700','#FFE082'),8:('#6D4C41','#BCAAA4'),9:('#C62828','#EF9A9A'),10:('#00A5CF','#A5E3F3')}
for i,(h,l) in ab_col.items(): hexc(f'vh{i}',h); hexc(f'vl{i}',l)
FLIP=np.array([-1.0,-1.0,1.0])
cmd.load('target_prep.pdb','tgt'); cmd.load_coordset(cmd.get_coords('tgt',1)*FLIP,'tgt',1)
base={}
for i in range(1,NAB+1):
    cmd.load(f'ab{i}_prep.pdb',f'ab{i}'); base[i]=cmd.get_coords(f'ab{i}',1).copy()*FLIP; cmd.load_coordset(base[i],f'ab{i}',1)
    cmd.hide('everything',f'ab{i}'); cmd.show('cartoon',f'ab{i}')
    cmd.color(f'vh{i}',f'ab{i} and chain A'); cmd.color(f'vl{i}',f'ab{i} and chain B')
cmd.hide('everything','tgt'); cmd.show('surface','tgt'); PAL={'A':'#656A40','B':'#5C8E98','C':'#78779E','D':'#67A378','E':'#906436','F':'#A66D78'}
for c,h in PAL.items():
    cmd.set_color('pc'+c,[int(h[i:i+2],16)/255 for i in (1,3,5)]); cmd.color('pc'+c,'tgt and chain '+c)
cmd.color('epi','tgt and ((chain B and resi 2-12) or (chain E and resi 132-147))')
S=8.0; Y0=548
D=(H/S)/(2*np.tan(np.radians(10))); ty=(H/2-Y0)/S
cmd.set_view((1,0,0,0,1,0,0,0,1,0,ty,-D,0,0,0,D-400,D+400,20))
appr={}
for i in range(1,NAB+1):
    v=base[i].mean(0).copy(); v[1]=0; appr[i]=v/np.linalg.norm(v)
FACE=92.0
def ease_io(u): u=min(max(u,0),1); return u*u*(3-2*u)
def theta(t):
    if t<T0: return FACE-360.0+360.0*ease_io(t/T0)
    return FACE+16.0*np.sin(2*np.pi*(t-T0)/9.0)
cur=0.0
def rot_to(a):
    global cur
    d=a-cur
    if abs(d)>1e-9: cmd.turn('y',d); cur=a
def alpha(t,j):
    st=T0+j*SLOT
    return 1.0 if st-1e-9<=t<st+SLOT-1e-9 else 0.0
nslot=int((30-T0)/SLOT+1e-6)
T=time.time()
FR=[int(x) for x in sys.argv[4].split(',')] if len(sys.argv)>4 else range(f0,f1)
for f in FR:
    t=f/FPS; rot_to(theta(t))
    act={}
    for j in range(nslot):
        a=alpha(t,j)
        if a>0: act[j%NAB+1]=(a,j)
    for i in range(1,NAB+1):
        if i in act:
            a,j=act[i]; s=T0+j*SLOT; pin=ease_io((t-s)/0.5)
            cmd.load_coordset(base[i]+appr[i]*18.0*(1-pin)**2,f'ab{i}',1)
            cmd.set('cartoon_transparency',1.0-a,f'ab{i}'); cmd.enable(f'ab{i}')
        else: cmd.disable(f'ab{i}')
    cmd.ray(W,H); cmd.png(f'frames/f{f:04d}.png',W,H); print('frame',f,'%.1f'%(time.time()-T),flush=True)
cmd.quit()
