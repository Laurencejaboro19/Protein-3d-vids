"""Independent check of glp1r_k/: reads the written PDBs (not the docking code) and reports identity, site and contact."""
import os, csv, json, sys
import numpy as np, gemmi
from scipy.spatial import cKDTree
os.chdir(os.path.dirname(os.path.abspath(__file__)))
HOT = {"bridge": [32, 39, 69, 88, 91, 121, 197, 201, 205, 210, 211, 214, 215, 221, 298, 299, 300, 306],
       "deep": [298, 299, 300, 306, 230, 233, 234, 309, 310]}
T = {r["priority_rank"]: r for r in csv.DictReader(open("top20.csv"))}
m = json.load(open("glp1r_k/meta.json"))
tg = gemmi.read_structure("glp1r_k/target.pdb")[0]["A"]
P = np.array([a.pos.tolist() for r in tg for a in r]); rn = np.array([r.seqid.num for r in tg for a in r]); tree = cKDTree(P)
bad = 0
print("vid rank site   len seq_ok site_ok  atoms<4.5 res<4.5 minD clash<2.5  own_hot(4.5A) own_hot(6.5A) other_hot(4.5A)")
for j, (rk, site) in enumerate(zip(m["ranks"], m["sites"])):
    ch = gemmi.read_structure("glp1r_k/b%02d.pdb" % j)[0]["B"]
    seq = gemmi.one_letter_code([r.name for r in ch]); X = np.array([a.pos.tolist() for r in ch for a in r])
    d, ii = tree.query(X)
    own = lambda c, s: len({rn[i] for i in tree.query_ball_point(X, c) for i in i} & set(HOT[s])) / len(HOT[s])
    other = "deep" if site == "bridge" else "bridge"
    seq_ok = seq == T[str(rk)]["sequence"]; site_ok = site == T[str(rk)]["site"]
    clash = int((d < 2.5).sum()); touch = int((d < 4.5).sum()); resn = len({rn[i] for l in tree.query_ball_point(X, 4.5) for i in l})
    ok = seq_ok and site_ok and clash == 0 and touch >= 8; bad += (not ok)
    print("%2d  %4d %-6s %3d %-6s %-7s %8d %7d %5.1f %5d      %.2f          %.2f          %.2f   %s" % (j + 1, rk, site, len(seq), seq_ok, site_ok, touch, resn, d.min(), clash, own(4.5, site), own(6.5, site), own(4.5, other), "" if ok else "<-- CHECK"))
print("binders:", len(m["ranks"]), "ranks unique:", len(set(m["ranks"])) == len(m["ranks"]), "problems:", bad)
