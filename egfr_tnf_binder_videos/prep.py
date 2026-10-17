import os; os.chdir(os.path.dirname(os.path.abspath(__file__)))
import gemmi, glob, numpy as np, os, re, json, sys
def kabsch(P,Q):  # find R,t so that R@P+t ~ Q
    pc,qc=P.mean(0),Q.mean(0);H=(P-pc).T@(Q-qc);U,S,Vt=np.linalg.svd(H);d=np.sign(np.linalg.det(Vt.T@U.T))
    D=np.diag([1,1,d]);R=Vt.T@D@U.T;return R,qc-R@pc
def rot(axis,deg):
    a=np.radians(deg);c,s=np.cos(a),np.sin(a)
    if axis=='y':return np.array([[c,0,s],[0,1,0],[-s,0,c]])
    if axis=='x':return np.array([[1,0,0],[0,c,-s],[0,s,c]])
def align_to_z(v):
    v=v/np.linalg.norm(v);z=np.array([0,0,1.]);ax=np.cross(v,z);n=np.linalg.norm(ax)
    if n<1e-8:return np.eye(3)
    ax/=n;ang=np.arccos(np.clip(v@z,-1,1));K=np.array([[0,-ax[2],ax[1]],[ax[2],0,-ax[0]],[-ax[1],ax[0],0]])
    return np.eye(3)+np.sin(ang)*K+(1-np.cos(ang))*K@K
def run(name,files,tchains,bchain,start_y,tilt_x,c3=False):
    out=f'{name}';os.makedirs(out,exist_ok=True)
    sts=[gemmi.read_structure(f) for f in files]
    for st in sts: st.setup_entities(); st.remove_hydrogens()
    def cas(st,chs):
        a=[]
        for c in st[0]:
            if c.name in chs:
                for r in c:
                    for at in r:
                        if at.name=='CA':a.append(at.pos.tolist())
        return np.array(a)
    ref=cas(sts[0],tchains);tx=[]
    # transform every complex onto ref target frame
    xf=[]
    for st in sts:
        P=cas(st,tchains);assert len(P)==len(ref),(len(P),len(ref));R,t=kabsch(P,ref);xf.append((R,t))
    bin_all=[]
    bpos=[]
    def bca(st):return np.array([a.pos.tolist() for c in st[0] if c.name==bchain for r in c for a in r if a.name=='CA'])
    if c3:
        cA,cB,cC=[cas(sts[0],[x]) for x in tchains]
        R1,t1=kabsch(cA,cB);chk=np.sqrt(((((R1@cB.T).T+t1)-cC)**2).sum(1).mean())
        print('C3 check A->B then B->C rmsd',round(float(chk),2))
        ops=[(np.eye(3),np.zeros(3)),(R1,t1),(R1@R1,R1@t1+t1)]
        # choose, for every binder, the symmetry copy that lands in the same groove as binder 0
        newxf=[];ref_c=None;used=[]
        for i,(st,(R,t)) in enumerate(zip(sts,xf)):
            b=(R@bca(st).T).T+t;best=None
            for k,(Rs,ts) in enumerate(ops):
                bb=(Rs@b.T).T+ts;c=bb.mean(0)
                if ref_c is None: best=(0,Rs,ts,c);break
                d=np.linalg.norm(c-ref_c)
                if best is None or d<best[0]:best=(d,Rs,ts,c)
            if ref_c is None:ref_c=best[3]
            used.append(int(np.argmin([np.linalg.norm(((Rs@b.T).T+ts).mean(0)-ref_c) for Rs,ts in ops])))
            newxf.append((best[1]@R,best[1]@t+best[2]))
        print('symmetry copy used per binder',used)
        bxf=newxf
    else:
        bxf=xf
    for st,(R,t) in zip(sts,bxf):
        bpos.append((R@bca(st).T).T+t)
    cen=ref.mean(0);vb=np.vstack(bpos).mean(0)-cen
    M=rot('x',tilt_x)@rot('y',start_y)@align_to_z(vb)  # site faces camera, then 3/4 view
    def tr(R,t,p):return M@((R@p+t)-cen)
    def write(st,R,t,chains,fn):
        L=[];n=1
        for c in st[0]:
            if c.name not in chains:continue
            for r in c:
                for a in r:
                    p=tr(R,t,np.array(a.pos.tolist()))
                    L.append("ATOM  %5d %-4s %3s %s%4d    %8.3f%8.3f%8.3f  1.00  0.00          %2s"%(n%100000,a.name if len(a.name)==4 else ' '+a.name,r.name,c.name,r.seqid.num,p[0],p[1],p[2],a.element.name.upper()));n+=1
            L.append('TER')
        open(fn,'w').write('\n'.join(L)+'\nEND\n')
    write(sts[0],*xf[0],set(tchains),f'{out}/target.pdb')
    for i,(st,(R,t)) in enumerate(zip(sts,bxf)):
        write(st,R,t,{bchain},f'{out}/b{i:02d}.pdb')
    json.dump({'n':len(files),'files':[os.path.basename(os.path.dirname(f)) if 'egfr' in name else os.path.basename(f) for f in files]},open(f'{out}/meta.json','w'))
    print(name,len(files),'binders; centroid dist',np.linalg.norm(vb).round(1))
ef=sorted(glob.glob('egfr_src/egfr_h409_night1_winners/structures/*/human_complex.cif'))
tf=sorted(glob.glob('tnf_src/*/structures/*_human.cif'),key=lambda f:int(re.search(r'_r(\d+)_human',f).group(1)))
run('egfr',ef,['A'],'B',-25,-8)
run('tnf',tf,['A','B','C'],'D',-25,-8,c3=True)
