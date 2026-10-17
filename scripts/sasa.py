import gemmi, numpy as np
from scipy.spatial import cKDTree
def sasa_atoms(X,elems,probe=1.4,n=120):
    rad={'C':1.7,'N':1.55,'O':1.52,'S':1.8}
    r=np.array([rad.get(e,1.7) for e in elems])+probe
    gold=np.pi*(3-np.sqrt(5)); k=np.arange(n)
    z=1-2*(k+0.5)/n; rr=np.sqrt(1-z*z); ph=gold*k
    sph=np.stack([rr*np.cos(ph),rr*np.sin(ph),z],1)
    tree=cKDTree(X); out=np.zeros(len(X))
    for i in range(len(X)):
        nb=[j for j in tree.query_ball_point(X[i],r[i]+r.max()) if j!=i]
        pts=X[i]+sph*r[i]
        if nb:
            d=np.linalg.norm(pts[:,None,:]-X[nb][None],axis=2)
            free=~(d<r[nb][None]).any(1)
        else: free=np.ones(n,bool)
        out[i]=free.mean()*4*np.pi*r[i]**2
    return out
if __name__=='__main__':
    t=gemmi.read_structure('inputs/8EJE_boltz_ABCDEF.pdb')
    X=[];M=[];E=[]
    for ch in t[0]:
        for r in ch:
            for a in r:
                if a.element.name!='H': X.append(a.pos.tolist());M.append((ch.name,r.seqid.num,r.name,a.name));E.append(a.element.name)
    X=np.array(X); s=sasa_atoms(X,E)
    np.save('tgt_sasa.npy',s)
    res={}
    for m,v in zip(M,s):
        if (m[0]=='B' and 2<=m[1]<=12) or (m[0]=='E' and 132<=m[1]<=147): res[(m[0],m[1],m[2])]=res.get((m[0],m[1],m[2]),0)+v
    for k,v in sorted(res.items()): print(k,round(v,1))
