import csv,json,numpy as np,gemmi
from scipy.spatial import cKDTree
import os; os.chdir(os.path.dirname(os.path.abspath(__file__)))
rows={int(r["rank_preference"]):r for r in csv.DictReader(open("top20.csv",encoding="utf-8-sig"))}
TGT="QVKDSAQNSVIIVDKNGRLVYLVENPGGYVAYSKAATVTGKLVHANFGTKKDFEDLYTPVNGSIVIVRAGKITFAEKVANAESLNAIGVLIYMDQTKFPIVNAELSFFGHAHLGTGDPYTPGFPSFNHTQFPPSRSSGLPNIPVQTISRAAAEKLFGNMEGDCPSDWKTDSTCRMVTSESKNVKLTVSNVLKE"
HOT=[int(x) for x in open('hotspots.txt').read().replace(' ','').split(',') if x]   # your design hotspots (UniProt numbers), comma-separated, kept out of the repo
def seq(ch): return "".join(gemmi.find_tabulated_residue(r.name).one_letter_code.upper() for r in ch)
ref=None
for k in range(1,21):
    m=gemmi.read_structure("bz/rank%02d.cif"%k)[0]; A=m["A"];B=m["B"]
    sa,sb=seq(A),seq(B)
    ca=np.array([r["CA"][0].pos.tolist() for r in A])
    if ref is None: ref=ca
    sp=gemmi.superpose_positions([gemmi.Position(*x) for x in ref],[gemmi.Position(*x) for x in ca])
    atA=[(r.seqid.num+190,a.pos.tolist()) for r in A for a in r if a.element.name!="H"]
    atB=[(r.seqid.num,a.pos.tolist()) for r in B for a in r if a.element.name!="H"]
    tA=cKDTree([p for n,p in atA]); d,i=tA.query([p for n,p in atB])
    cont=set(atA[j][0] for q,j in enumerate(i) if d[q]<4.5)
    cont=set()
    tB=cKDTree([p for n,p in atB])
    for n,p in atA:
        if tB.query_ball_point(p,4.5): cont.add(n)
    ib=set(atB[q][0] for q in range(len(atB)) if d[q]<4.5)
    hot=[h for h in HOT if h in cont]
    r=rows[k]
    print("rank%2d tgt_ok=%s binder_ok=%s lenB=%d fitRMSD=%.2f minD=%.1f targetIface=%d binderIface=%d hot=%d/5 %s | csv_hot=%s"%(k,sa==TGT,sb==r["sequence"],len(sb),sp.rmsd,d.min(),len(cont),len(ib),len(hot),hot,r["hotspots_hit_human_of5"]))
