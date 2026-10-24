import os,sys,csv,glob,numpy as np,gemmi
from scipy.spatial import cKDTree
os.chdir(os.path.dirname(os.path.abspath(__file__)))
HOT={"bridge":[32,39,69,88,91,121,197,201,205,210,211,214,215,221,298,299,300,306],"deep":[298,299,300,306,230,233,234,309,310]}
T={int(r["priority_rank"]):r for r in csv.DictReader(open("top20.csv"))}
ref=gemmi.read_structure("6X18.pdb")[0]["R"]
refca={r.seqid.num:np.array(r["CA"][0].pos.tolist()) for r in ref if "CA" in [a.name for a in r]}
# GLP-1 footprint on 6X18 for comparison
pep=gemmi.read_structure("6X18.pdb")[0]["P"]; rt=cKDTree(np.array([a.pos.tolist() for r in ref for a in r])); rnum=np.array([r.seqid.num for r in ref for a in r])
fp=set(); 
for r in pep:
    for a in r:
        for i in rt.query_ball_point(a.pos.tolist(),4.5): fp.add(int(rnum[i]))
print("GLP-1 footprint residues:",len(fp))
rows=[]
for k in range(1,21):
    st=gemmi.read_structure("bz/rank%02d.cif"%k); m=st[0]; A=m["A"]; B=m["B"]
    seqA=gemmi.one_letter_code([r.name for r in A]); seqB=gemmi.one_letter_code([r.name for r in B])
    ok=seqB==T[k]["sequence"]
    X=[(r.seqid.num+23,a) for r in A for a in r]; rn=np.array([x[0] for x in X]); P=np.array([x[1].pos.tolist() for x in X]); tr=cKDTree(P)
    Bx=np.array([a.pos.tolist() for r in B for a in r]); d,_=tr.query(Bx)
    cont=sorted({int(rn[i]) for l in tr.query_ball_point(Bx,4.5) for i in l})
    hb=[h for h in HOT["bridge"] if h in cont]; hd=[h for h in HOT["deep"] if h in cont]
    # region contacts
    def reg(n): return "ECD" if n<130 else "linker" if n<145 else "TM1" if n<169 else "TM2/ECL1" if n<226 else "TM3" if n<257 else "TM4" if n<291 else "ECL2" if n<303 else "TM5" if n<338 else "TM6/ECL3" if n<378 else "TM7"
    regs={}
    for n in cont: regs[reg(n)]=regs.get(reg(n),0)+1
    # superpose receptor onto 6X18 (CA, common residues) for frame + conformation check
    ca={r.seqid.num+23:np.array(r["CA"][0].pos.tolist()) for r in A}
    com=[n for n in ca if n in refca and 145<=n<=390]
    a=np.array([ca[n] for n in com]); b=np.array([refca[n] for n in com])
    rms=gemmi.superpose_positions([gemmi.Position(*x) for x in b],[gemmi.Position(*x) for x in a])
    rows.append((k,T[k]["site"],len(seqB),ok,len(cont),len(hb),len(hd),rms.rmsd,len(set(cont)&fp),float(d.min()),regs))
    print("r%02d %-6s len%3d seq_ok %s | res<4.5 %2d | bridge hot %2d/18 deep hot %d/9 | TMrmsd vs 6X18 %.1f | GLP1 fp overlap %2d | minD %.1f | %s"%(k,T[k]["site"],len(seqB),ok,len(cont),len(hb),len(hd),rms.rmsd,len(set(cont)&fp),d.min(),regs),flush=True)
