"""Each Boltz-2.1 complex (receptor chain A + binder chain B) is placed in the 6X18 frame by superposing receptor CA 145-390 (TM core)."""
import os,csv,json,numpy as np,gemmi
from scipy.spatial import cKDTree
os.chdir(os.path.dirname(os.path.abspath(__file__)))
BZ="bz"
HOT={"bridge":[32,39,69,88,91,121,197,201,205,210,211,214,215,221,298,299,300,306],"deep":[298,299,300,306,230,233,234,309,310]}
T={int(r["priority_rank"]):r for r in csv.DictReader(open("top20.csv"))}
R18=gemmi.read_structure("6X18.pdb")[0]["R"]
refca={r.seqid.num:np.array(r["CA"][0].pos.tolist()) for r in R18 if r.het_flag=="A"}
cen=np.array(list(refca.values())).mean(0)
def pdbl(rb,chain): return ["ATOM  %5d %-4s %3s %s%4d    %8.3f%8.3f%8.3f  1.00  0.00          %2s"%(n%100000,an if len(an)==4 else " "+an,rn,chain,rs,p[0],p[1],p[2],el) for n,(rn,rs,an,el,p) in enumerate(rb,1)]
os.makedirs("glp1r_bz",exist_ok=True)
order=list(range(1,21))
cents={"bridge":[],"deep":[]}; allcen=[]
for j,k in enumerate(order):
    m=gemmi.read_structure("%s/rank%02d.cif"%(BZ,k))[0]; A=m["A"]; B=m["B"]
    cas={r.seqid.num+23:np.array(r["CA"][0].pos.tolist()) for r in A}
    com=[n for n in cas if n in refca and 145<=n<=390]
    sp=gemmi.superpose_positions([gemmi.Position(*refca[n]) for n in com],[gemmi.Position(*cas[n]) for n in com])
    M=np.array(sp.transform.mat.tolist()); v=np.array(sp.transform.vec.tolist())
    def conv(ch,off):
        return [(r.name,r.seqid.num+off,a.name,a.element.name.upper(),((np.array(a.pos.tolist())@M.T)+v)-cen) for r in ch for a in r if a.element.name!="H"]
    Ra=conv(A,23); Bb=conv(B,0)
    open("glp1r_bz/r%02d.pdb"%j,"w").write("\n".join(pdbl(Ra,"A"))+"\nEND\n")
    open("glp1r_bz/b%02d.pdb"%j,"w").write("\n".join(pdbl(Bb,"B"))+"\nEND\n")
    cents[T[k]["site"]].append(np.mean([x[4] for x in Bb],0)); allcen.append([x[4] for x in Bb])
    print("vid%2d rank%2d TM-core fit rmsd %.2f"%(j+1,k,sp.rmsd),flush=True)
ca=np.array([refca[n] for n in sorted(refca)])-cen; ns=np.array(sorted(refca))
axis=np.linalg.svd(ca-ca.mean(0))[2][0]
if ca[ns<130].mean(0)@axis<ca[ns>300].mean(0)@axis: axis=-axis
cl=[np.mean(c,0).tolist() for c in allcen]
json.dump({"cent":cl,"iptm":[float(T[k]["iptm"]) for k in order],"ipsae":[float(T[k]["ipsae"]) for k in order],"n":len(order),"ranks":order,"sites":[T[k]["site"] for k in order],"dirs":{s:np.mean(v,0).tolist() for s,v in cents.items() if v},"axis":axis.tolist()},open("glp1r_bz/meta.json","w"))

