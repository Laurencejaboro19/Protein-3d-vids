"""Each Boltz-2.1 refold of the KRAS G12D pMHC + binder (chains A HLA-A*11:01, B b2m, C peptide VVVGADGVGK, D binder)
is placed in the rank-1 frame by superposing HLA CA atoms (iterative trimming of the most deviant 25% x3).
Usage: python3 build_kras.py <workdir>   (workdir holds bz/rankNN.cif and top20.csv)
Writes <workdir>/kras_bz/{t_hla.pdb,t_pep.pdb,bNN.pdb,meta.json}"""
import csv,json,os,sys,numpy as np,gemmi
W=sys.argv[1] if len(sys.argv)>1 else "."
os.makedirs(W+"/kras_bz",exist_ok=True)
T={int(r["rank"]):r for r in csv.DictReader(open(W+"/top20.csv",encoding="utf-8-sig"))}
def pdbl(rb,chain): return ["ATOM  %5d %-4s %3s %s%4d    %8.3f%8.3f%8.3f  1.00  0.00          %2s"%(n%100000,an if len(an)==4 else " "+an,rn,chain,rs%10000,p[0],p[1],p[2],el) for n,(rn,rs,an,el,p) in enumerate(rb,1)]
S={k:gemmi.read_structure(W+"/bz/rank%02d.cif"%k)[0] for k in range(1,21)}
caof=lambda ch:np.array([r["CA"][0].pos.tolist() for r in ch])
ref=caof(S[1]["A"]); cen=ref.mean(0)
def atoms(ch,M,v): return [(r.name,r.seqid.num,a.name,a.element.name.upper(),((np.array(a.pos.tolist())@M.T)+v)-cen) for r in ch for a in r if a.element.name!="H"]
I=(np.eye(3),np.zeros(3))
hla=atoms(S[1]["A"],*I); b2m=atoms(S[1]["B"],*I); pep=atoms(S[1]["C"],*I)
open(W+"/kras_bz/t_hla.pdb","w").write("\n".join(pdbl(hla,"A")+pdbl(b2m,"B"))+"\nEND\n")
open(W+"/kras_bz/t_pep.pdb","w").write("\n".join(pdbl(pep,"C"))+"\nEND\n")
cents=[]; pepc=np.mean([x[4] for x in pep],0)
for j,k in enumerate(range(1,21)):
    m=S[k];ca=caof(m["A"]);idx=np.arange(len(ref))
    for it in range(4):
        sp=gemmi.superpose_positions([gemmi.Position(*ref[i]) for i in idx],[gemmi.Position(*ca[i]) for i in idx])
        M=np.array(sp.transform.mat.tolist());v=np.array(sp.transform.vec.tolist())
        d=np.linalg.norm((ca@M.T+v)-ref,axis=1); idx=np.argsort(d)[:int(len(ref)*0.75)]
    allr=float(np.sqrt((d**2).mean()))
    Bb=atoms(m["D"],M,v)
    open(W+"/kras_bz/b%02d.pdb"%j,"w").write("\n".join(pdbl(Bb,"D"))+"\nEND\n")
    cents.append(np.mean([x[4] for x in Bb],0).tolist())
    print("vid%2d rank%2d core(75%%) rmsd %.2f all-CA rmsd %.2f"%(j+1,k,sp.rmsd,allr))
# vertical axis = long axis of HLA+b2m (roughly the groove normal), signed to point from the platform toward the peptide
cab=np.vstack([ref-cen,caof(S[1]["B"])-cen]); cab0=cab-cab.mean(0)
axis=np.linalg.svd(cab0)[2][0]
if np.dot(pepc-cab.mean(0),axis)<0: axis=-axis
f=lambda x:float(x)
json.dump({"cent":cents,"n":20,"ranks":list(range(1,21)),"axis":axis.tolist(),
 "ids":[T[k]["id"] for k in range(1,21)],"lens":[int(T[k]["len"]) for k in range(1,21)],"tier":[T[k]["tier"] for k in range(1,21)],
 "g":[f(T[k]["g_ipsae"]) for k in range(1,21)],"wt":[f(T[k]["wt_ipsae_max"]) for k in range(1,21)],"pf":[f(T[k]["pf_ipsae_max"]) for k in range(1,21)],
 "iptm":[f(T[k]["g_iptm"]) for k in range(1,21)]},open(W+"/kras_bz/meta.json","w"))
