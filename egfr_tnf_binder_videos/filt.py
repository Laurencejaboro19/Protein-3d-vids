import os; os.chdir(os.path.dirname(os.path.abspath(__file__)))
import numpy as np,glob,json,os,shutil
from scipy.spatial import cKDTree
def ca(fn):return np.array([[float(l[30:38]),float(l[38:46]),float(l[46:54])] for l in open(fn) if l.startswith('ATOM') and l[12:16].strip()=='CA'])
for n in ('egfr','tnf'):
    t=ca(f'{n}/target.pdb');kd=cKDTree(t);fs=sorted(glob.glob(f'{n}/b[0-9]*.pdb'));meta=json.load(open(f'{n}/meta.json'))
    cs=np.array([ca(f).mean(0) for f in fs]);med=np.median(cs,0)
    keep=[]
    for i,f in enumerate(fs):
        d=float(kd.query(ca(f))[0].min());off=float(np.linalg.norm(cs[i]-med))
        ok=d>=3.5 and off<=14
        keep.append(ok)
    print(n,'kept',sum(keep),'of',len(fs),'dropped idx',[i for i,k in enumerate(keep) if not k])
    names=[m for m,k in zip(meta['files'],keep) if k]
    os.makedirs(f'{n}_k',exist_ok=True)
    shutil.copy(f'{n}/target.pdb',f'{n}_k/target.pdb')
    j=0
    for f,k in zip(fs,keep):
        if k: shutil.copy(f,f'{n}_k/b{j:02d}.pdb');j+=1
    json.dump({'n':j,'files':names},open(f'{n}_k/meta.json','w'))
