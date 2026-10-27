"""Each Boltz-2.1 complex (target chain A + binder chain B) is placed in the rank-1 target frame by superposing target CA atoms (iterative trimming of the most deviant 25% x3)."""
import csv,json,os,numpy as np,gemmi
os.makedirs("tfr1_bz",exist_ok=True)
T={int(r["rank_preference"]):r for r in csv.DictReader(open("top20.csv",encoding="utf-8-sig"))}
def pdbl(rb,chain): return ["ATOM  %5d %-4s %3s %s%4d    %8.3f%8.3f%8.3f  1.00  0.00          %2s"%(n%100000,an if len(an)==4 else " "+an,rn,chain,rs,p[0],p[1],p[2],el) for n,(rn,rs,an,el,p) in enumerate(rb,1)]
S={k:gemmi.read_structure("bz/rank%02d.cif"%k)[0] for k in range(1,21)}
caof=lambda m:np.array([r["CA"][0].pos.tolist() for r in m["A"]])
ref=caof(S[1]); cen=ref.mean(0)
cents=[];info=[]
for j,k in enumerate(range(1,21)):
    m=S[k];A=m["A"];B=m["B"];ca=caof(m)
    idx=np.arange(len(ref))
    for it in range(4):
        sp=gemmi.superpose_positions([gemmi.Position(*ref[i]) for i in idx],[gemmi.Position(*ca[i]) for i in idx])
        M=np.array(sp.transform.mat.tolist());v=np.array(sp.transform.vec.tolist())
        d=np.linalg.norm((ca@M.T+v)-ref,axis=1)
        idx=np.argsort(d)[:int(len(ref)*(0.75 if it<3 else 0.75))]
    core=sp.rmsd; allr=float(np.sqrt(((((ca@M.T+v)-ref)**2).sum(1)).mean()))
    conv=lambda ch,off:[(r.name,r.seqid.num+off,a.name,a.element.name.upper(),((np.array(a.pos.tolist())@M.T)+v)-cen) for r in ch for a in r if a.element.name!="H"]
    Ra=conv(A,190);Bb=conv(B,0)
    open("tfr1_bz/r%02d.pdb"%j,"w").write("\n".join(pdbl(Ra,"A"))+"\nEND\n")
    open("tfr1_bz/b%02d.pdb"%j,"w").write("\n".join(pdbl(Bb,"B"))+"\nEND\n")
    cents.append(np.mean([x[4] for x in Bb],0).tolist())
    info.append((k,core,allr)); print("vid%2d rank%2d core(75%%) rmsd %.2f all-CA rmsd %.2f"%(j+1,k,core,allr))
ca=ref-cen; axis=np.linalg.svd(ca-ca.mean(0))[2][0]
src=lambda s:"BindCraft2" if s.startswith("BC2") else "RFD4-Proteina"
def f(x):
    try:return float(x)
    except:return None
json.dump({"cent":cents,"n":20,"ranks":list(range(1,21)),"axis":axis.tolist(),
 "sites":[src(T[k]["name"]) for k in range(1,21)],
 "iptm":[f(T[k]["iptm_human"]) for k in range(1,21)],"ipsae":[f(T[k]["ipsae_human"]) for k in range(1,21)],
 "ph":[f(T[k]["ph_fold_release_x_human"]) for k in range(1,21)]},open("tfr1_bz/meta.json","w"))
