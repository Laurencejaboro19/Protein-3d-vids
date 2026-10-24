"""Schematic poses: idealised helical binders (real sequences, backbone only) hand-docked on 6X18 chain R
at the bridge / deep hotspot sites by rigid-body search. NOT predicted structures."""
import os, sys, csv, json
import numpy as np, gemmi
from scipy.spatial import cKDTree
from scipy.spatial.transform import Rotation as Rot
os.chdir(os.path.dirname(os.path.abspath(__file__)))
HOT = {"bridge": [32, 39, 69, 88, 91, 121, 197, 201, 205, 210, 211, 214, 215, 221, 298, 299, 300, 306],
       "deep": [298, 299, 300, 306, 230, 233, 234, 309, 310]}
ONE2THREE = dict(zip("ACDEFGHIKLMNPQRSTVWY", "ALA CYS ASP GLU PHE GLY HIS ILE LYS LEU MET ASN PRO GLN ARG SER THR VAL TRP TYR".split()))
def nerf(a, b, c, bond, ang, tor):
    ang, tor = np.radians(ang), np.radians(tor)
    bc = c - b; bc /= np.linalg.norm(bc)
    n = np.cross(b - a, bc); n /= np.linalg.norm(n)
    m = np.cross(n, bc)
    d = np.array([-bond * np.cos(ang), bond * np.sin(ang) * np.cos(tor), bond * np.sin(ang) * np.sin(tor)])
    return c + d[0] * bc + d[1] * m + d[2] * n
def helix(n, phi=-57., psi=-47.):
    N = np.array([0., 0., 0.]); CA = np.array([1.458, 0., 0.])
    C = CA + 1.525 * np.array([np.cos(np.radians(180 - 111.0)), np.sin(np.radians(180 - 111.0)), 0.])
    res = []
    for i in range(n):
        O = nerf(N, CA, C, 1.231, 120.8, psi + 180)
        res.append([N, CA, C, O])
        if i == n - 1: break
        Nn = nerf(N, CA, C, 1.329, 116.2, psi)
        CAn = nerf(CA, C, Nn, 1.458, 121.7, 180.)
        Cn = nerf(C, Nn, CAn, 1.525, 111.0, phi)
        N, CA, C = Nn, CAn, Cn
    return np.array(res)            # n x 4 x 3
def orient_z(res, up=True):
    ca = res[:, 1]; c = ca.mean(0)
    u, s, vt = np.linalg.svd(ca - c); ax = vt[0]
    if np.dot(ca[-1] - ca[0], ax) < 0: ax = -ax
    z = np.array([0, 0, 1.]); v = np.cross(ax, z); sn = np.linalg.norm(v)
    R = Rot.identity() if sn < 1e-8 else Rot.from_rotvec(v / sn * np.arccos(np.clip(np.dot(ax, z), -1, 1)))
    out = R.apply((res - c).reshape(-1, 3)).reshape(res.shape)
    if not up: out = out * np.array([1, -1, -1])
    return out
def build(L):
    nh = 2 if L <= 40 else 3
    loops = 3 * (nh - 1); rem = L - loops
    hl = [rem // nh + (1 if i < rem % nh else 0) for i in range(nh)]
    pos = [(-5., 0.), (5., 0.)] if nh == 2 else [(0., 5.8), (-5., -2.9), (5., -2.9)]
    H = []
    for i in range(nh):
        h = orient_z(helix(hl[i]), up=(i % 2 == 0))
        h = h + np.array([pos[i][0], pos[i][1], 0.]); H.append(h)
    out = []
    for i in range(nh):
        out.extend(list(H[i]))
        if i < nh - 1:
            a = H[i][-1, 1]; b = H[i + 1][0, 1]
            zdir = np.array([0, 0, 1.]) * (1 if i % 2 == 0 else -1)
            ctrl = (a + b) / 2 + zdir * 7.0
            for k in range(1, 4):
                t = k / 4.; p = (1 - t) ** 2 * a + 2 * (1 - t) * t * ctrl + t * t * b
                tang = 2 * (1 - t) * (ctrl - a) + 2 * t * (b - ctrl); tang /= np.linalg.norm(tang)
                perp = np.cross(tang, np.array([1., 0, 0])); perp /= np.linalg.norm(perp)
                out.append(np.array([p - 1.4 * tang, p, p + 1.4 * tang, p + 1.4 * tang + 1.2 * perp]))
    out = np.array(out); assert len(out) == L
    return out - out[:, 1].mean(0)

st = gemmi.read_structure("6X18.pdb"); R18 = st[0]["R"]
rows = []
for r in R18:
    if r.het_flag != "A": continue
    for a in r: rows.append((r.name, r.seqid.num, a.name, a.element.name.upper(), np.array(a.pos.tolist())))
P = np.array([x[4] for x in rows]); resnum = np.array([x[1] for x in rows])
cen = np.array([x[4] for x in rows if x[2] == "CA"]).mean(0)
Pc = P - cen
tree = cKDTree(Pc)
site_idx = {s: np.where(np.isin(resnum, HOT[s]))[0] for s in HOT}
site_cen = {s: Pc[site_idx[s]].mean(0) for s in HOT}
site_tree = {s: cKDTree(Pc[site_idx[s]]) for s in HOT}
site_res = {s: resnum[site_idx[s]] for s in HOT}
def evaluate(X, site):
    d, _ = tree.query(X)
    clash = int((d < 3.0).sum()); contacts = int((d < 4.8).sum())
    dd, ii = site_tree[site].query(X, distance_upper_bound=(6.5 if site == 'deep' else 4.8))
    ok = np.isfinite(dd); hot = len(set(site_res[site][ii[ok]])) / len(set(HOT[site]))
    return hot, contacts, clash, d.min()
hot_trees = {s_: [cKDTree(Pc[resnum == h]) for h in HOT[s_]] for s_ in HOT}
def score(X, site):
    d, _ = tree.query(X)
    cl = int((d < 3.0).sum()); c = int((d < 4.8).sum())
    soft = np.mean([np.clip((9.0 - t.query(X)[0].min()) / 5.0, 0, 1) for t in hot_trees[site]])   # 1 when a hotspot residue is within 4 A
    return 100 * soft + 0.2 * c - 30 * cl - 3 * max(0, 25 - c)
def search(B, site, rng, nrand=9000, rad=22):
    if site == 'deep': nrand, rad = 30000, 26
    best = []
    for _ in range(nrand):
        Rm = Rot.random(random_state=rng.integers(1 << 30))
        t = site_cen[site] + rng.normal(size=3) / 1.7 * rad / 2
        X = Rm.apply(B) + t
        if tree.query(X)[0].min() < 2.6: continue
        best.append((score(X, site), Rm, t))
    best.sort(key=lambda x: -x[0]); best = best[:(30 if site == 'deep' else 12)]; fin = []
    for s, Rm, t in best:
        for it in range(500):
            dR = Rot.from_rotvec(rng.normal(size=3) * np.radians(4)); Rn = dR * Rm; tn = t + rng.normal(size=3) * 0.8
            X = Rn.apply(B) + tn; sn = score(X, site)
            if sn > s: s, Rm, t = sn, Rn, tn
        fin.append((s, Rm, t))
    fin.sort(key=lambda x: -x[0]); return fin[0]

AF = "af"
top = list(csv.DictReader(open("top20.csv")))
def load_binder(rank):
    import glob
    f = glob.glob("%s/fold_g%d/*_model_0.cif" % (AF, rank))
    if not f: return None
    ch = gemmi.read_structure(f[0])[0][0]; rowsB = []
    for r in ch:
        for at in r:
            if at.element.name == "H": continue
            rowsB.append((r.name, r.seqid.num, at.name, at.element.name.upper(), np.array(at.pos.tolist()), at.b_iso))
    return rowsB
items = []
for r in sorted(top, key=lambda r: int(r["priority_rank"])):
    b = load_binder(int(r["priority_rank"]))
    if b is None: print("MISSING fold for rank", r["priority_rank"]); continue
    items.append((r, b))
order = [x for x in items if x[0]["site"] == "bridge"] + [x for x in items if x[0]["site"] == "deep"]
os.makedirs("glp1r_k", exist_ok=True)
def pdb(rowsB, chain):
    L = []
    for n, (rn, resn, an, el, p) in enumerate(rowsB, 1):
        L.append("ATOM  %5d %-4s %3s %s%4d    %8.3f%8.3f%8.3f  1.00  0.00          %2s" % (n % 100000, an if len(an) == 4 else " " + an, rn, chain, resn, p[0], p[1], p[2], el))
    return L
open("glp1r_k/target.pdb", "w").write("\n".join(pdb([(a, b, c, d, p) for a, b, c, d, p in zip([x[0] for x in rows], resnum, [x[2] for x in rows], [x[3] for x in rows], Pc)], "A")) + "\nEND\n")
rng = np.random.default_rng(11); cents = {"bridge": [], "deep": []}
print("vid rank site  len pLDDT hot_own hot_other pairs clashes min_d")
for j, (r, b) in enumerate(order):
    site = r["site"]; other = "deep" if site == "bridge" else "bridge"
    X0 = np.array([x[4] for x in b]); X0 = X0 - X0.mean(0)
    s_, Rm, t = search(X0, site, rng)
    X = Rm.apply(X0) + t
    ho, c, cl, dm = evaluate(X, site); hx = evaluate(X, other)[0]
    plddt = np.mean([x[5] for x in b if x[2] == "CA"])
    rb = [(x[0], x[1], x[2], x[3], X[k]) for k, x in enumerate(b)]
    open("glp1r_k/b%02d.pdb" % j, "w").write("\n".join(pdb(rb, "B")) + "\nEND\n")
    cents[site].append(X.mean(0))
    print("%2d  %4s %-6s %3d  %4.0f   %.2f   %.2f     %4d     %d    %.1f" % (j, r["priority_rank"], site, len(set(x[1] for x in b)), plddt, ho, hx, c, cl, dm))
cav = np.array([x[4] for x in rows if x[2] == "CA"]) - cen
cres = np.array([x[1] for x in rows if x[2] == "CA"])
axis = np.linalg.svd(cav - cav.mean(0))[2][0]
if cav[cres < 130][:, :].mean(0) @ axis < cav[cres > 300].mean(0) @ axis: axis = -axis   # N-terminal domain up
axis = axis.tolist()
dirs = {k: np.mean(v, 0).tolist() for k, v in cents.items() if v}
json.dump({"n": len(order), "ranks": [int(r["priority_rank"]) for r, _ in order], "sites": [r["site"] for r, _ in order],
           "sources": ["AlphaFold Server"] * len(order), "dirs": dirs, "axis": axis}, open("glp1r_k/meta.json", "w"))
