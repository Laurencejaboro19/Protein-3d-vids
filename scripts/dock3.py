import gemmi, numpy as np, re, json
from scipy.spatial import cKDTree
from scipy.spatial.transform import Rotation as R
TGT="inputs/8EJE_boltz_ABCDEF.pdb"
t=gemmi.read_structure(TGT)
def atoms(st):
    X=[];M=[]
    for ch in st[0]:
        for r in ch:
            for a in r:
                if a.element.name!='H': X.append(a.pos.tolist());M.append((ch.name,r.seqid.num,a.name))
    return np.array(X),M
TX,TM=atoms(t); tree=cKDTree(TX); sasa=np.load('tgt_sasa.npy')
isepi=np.array([(m[0]=='B' and 2<=m[1]<=12) or (m[0]=='E' and 132<=m[1]<=147) for m in TM])
exp_idx=np.where(isepi&(sasa>15))[0]; EX=TX[exp_idx]; ew=sasa[exp_idx]
print('exposed epitope atoms',len(EX),'of',isepi.sum())
# outward normals
nrm=[]
for i in exp_idx:
    nb=tree.query_ball_point(TX[i],10.0); v=TX[i]-TX[nb].mean(0); nrm.append(v/np.linalg.norm(v))
u0=(np.array(nrm)*ew[:,None]).sum(0); u0/=np.linalg.norm(u0); ec=(EX*ew[:,None]).sum(0)/ew.sum()
print('patch centre',ec.round(1),'normal',u0.round(2))
def trim(a,b):
    k=2 if b-a>7 else 1
    return list(range(a+k,b-k))
def cdr_idx(seq,heavy):
    if heavy:
        a=re.search(r'C[A-Z][AVG]S',seq).end(); b=re.search(r'W[VI]R',seq).start()
        c=re.search(r'[LP]E[WL][VIM][GSA]',seq[b:]).end()+b; m=re.search(r'[KR][RG]?[RK]?F[TA]',seq[c:]) or re.search(r'R[VF][TA]',seq[c:]); d=m.start()+c
        e=re.search(r'YY?C',seq).end(); f=re.search(r'WGQG',seq).start()
    else:
        a=re.search(r'[IVL][ST]?C',seq).end(); b=re.search(r'W[YFL][QL]',seq).start()
        c=re.search(r'L+IY',seq).end(); d=re.search(r'G[IV]?P',seq[c:]).start()+c
        e=re.search(r'YYC',seq).end(); f=re.search(r'FG[QG]G',seq).start()
    return trim(a,b)+trim(c,d)+trim(e,f)
def score(X,cm,detail=False):
    d,_=tree.query(X); clash=np.sum(np.clip(2.8-d,0,None)**2)
    de,_=cKDTree(X[cm]).query(EX); cover=np.sum(ew*np.clip(de-4.2,0,None))/ew.sum()
    dc,_=tree.query(X[cm]); contact=np.mean(np.clip(dc-4.5,0,None))
    cc=X[cm].mean(0); pc=np.linalg.norm(cc-(ec+u0*9.0))
    s=3.0*clash+8.0*cover+0.4*contact+0.35*pc
    return (s,clash,cover,contact) if detail else s
rng=np.random.default_rng(11)
out={}
print('target point',(ec+u0*9.0).round(1))
NS=[int(x) for x in __import__('sys').argv[1].split(',')]
for n in NS:
    s=gemmi.read_structure(f"inputs/lasv_pdbs/lasv_{n}_model_0.pdb")
    AX,AM=atoms(s)
    seqs={ch.name:gemmi.one_letter_code([r.name for r in ch]) for ch in s[0]}
    cdr=set()
    for ch in s[0]:
        for i in cdr_idx(seqs[ch.name],ch.name=='A'): cdr.add((ch.name,ch[i].seqid.num))
    cm=np.array([(m[0],m[1]) in cdr for m in AM]); cen0=AX.mean(0)
    cands=[]
    for trial in range(2500):
        u=u0+rng.normal(0,0.55,3); u/=np.linalg.norm(u)
        X=R.random(random_state=int(rng.integers(1e9))).apply(AX-cen0)
        v=X[cm].mean(0); v/=np.linalg.norm(v)
        a=R.align_vectors([-u],[v])[0]; X=(R.from_rotvec(-u*rng.uniform(0,2*np.pi))*a).apply(X)
        X=X+ec+u*rng.uniform(8,20)-X[cm].mean(0)
        cands.append((score(X,cm),X))
    cands.sort(key=lambda z:z[0]); best=(1e9,None)
    for sc,X in cands[:12]:
        cur,cs=X.copy(),sc
        for it in range(300):
            c=cur.mean(0); new=R.from_rotvec(rng.normal(0,0.025,3)).apply(cur-c)+c+rng.normal(0,0.6,3)
            ns=score(new,cm)
            if ns<cs: cur,cs=new,ns
        if cs<best[0]: best=(cs,cur.copy())
    sc,X=best; det=score(X,cm,True)
    dd,_=cKDTree(X).query(EX); 
    print(n,'score %.2f clash %.2f cover %.2f contact %.2f'%det,'| exposed epitope atoms within 5A of antibody: %.0f%%'%(100*(dd<5).mean()),'min dist to target %.2f'%tree.query(X)[0].min(),flush=True)
    s2=s.clone(); k=0
    for ch in s2[0]:
        for r in ch:
            for a in r:
                if a.element.name!='H': a.pos=gemmi.Position(*X[k]); k+=1
    s2.write_pdb(f"ab{n}_docked.pdb")
