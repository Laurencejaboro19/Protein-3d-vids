import gemmi, numpy as np, json
from scipy.spatial.transform import Rotation as R
TGT="inputs/8EJE_boltz_ABCDEF.pdb"
t=gemmi.read_structure(TGT)
def cent(st,ch): return np.array([r['CA'][0].pos.tolist() for r in st[0][ch]]).mean(0)
allc=np.array([r['CA'][0].pos.tolist() for c in t[0] for r in c]).mean(0)
gp1=np.array([cent(t,c) for c in 'ABC']); gp2=np.array([cent(t,c) for c in 'DEF'])
ax=np.cross(gp1[1]-gp1[0],gp1[2]-gp1[0]); ax/=np.linalg.norm(ax)
print('3-fold axis',ax,'axis angle between GP1 and GP2 planes check',np.cross(gp2[1]-gp2[0],gp2[2]-gp2[0])@ax/np.linalg.norm(np.cross(gp2[1]-gp2[0],gp2[2]-gp2[0])))
# rotate axis -> +y
rot=R.align_vectors([[0,1,0]],[ax])[0]
def xf(st,write):
    s=st.clone()
    for ch in s[0]:
        for r in ch:
            for a in r:
                p=rot.apply(np.array(a.pos.tolist())-allc); a.pos=gemmi.Position(*p)
    s.write_pdb(write)
xf(t,'target_prep.pdb')
for n in range(1,11):
    xf(gemmi.read_structure(f'ab{n}_docked.pdb'),f'ab{n}_prep.pdb')
ec=np.array([r['CA'][0].pos.tolist() for r in t[0]['B'] if 2<=r.seqid.num<=12]+[r['CA'][0].pos.tolist() for r in t[0]['E'] if 132<=r.seqid.num<=147]).mean(0)
print('epitope centroid in prep frame',rot.apply(ec-allc))
