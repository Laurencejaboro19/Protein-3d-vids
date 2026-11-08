"""ipSAE + contact map for 20 TfR1 dimer refolds, run on Modal.
Usage:  modal run tfr1_dimer_ipsae.py --folder <dir with NN_<id> download folders> --out <csv path>
Each job folder must hold a structure .cif and a PAE .npz (either loose or inside prediction_archive*.tar.gz).
Chains: A,B = TfR1 (121-760, CIF numbering 1-640 -> UniProt = n+120), C = binder."""
import os, sys, glob, re, io, csv, json, tarfile, tempfile, subprocess
import modal

app = modal.App("pdfa-tfr1-ipsae")
image = (modal.Image.debian_slim(python_version="3.11")
         .apt_install("git").pip_install("numpy", "gemmi")
         .run_commands("git clone --depth 1 https://github.com/DunbrackLab/ipsae /opt/ipsae"))

DOMAINS = [("protease-like", 121, 188), ("apical", 189, 383), ("helical", 384, 605), ("protease-like", 606, 760)]
def domain_of(u):
    for n, a, b in DOMAINS:
        if a <= u <= b: return n
    return "other"

def score_core(files, binder="C", targets=("A", "B"), pae=10, dist=10, ipsae_py=None):
    """files: {basename: bytes} for one job. Returns one result dict."""
    ipsae_py = ipsae_py or os.environ.get("IPSAE_PY", "/opt/ipsae/ipsae.py")
    cif = [n for n in files if n.endswith(".cif")]
    paes = [n for n in files if n.endswith(".npz") and "pae" in os.path.basename(n).lower()]
    if not cif or not paes:
        return {"error": "missing cif or pae npz", "files": sorted(files)}
    cif = sorted(cif, key=lambda n: ("model_0" not in n and "sample_0" not in n, n))[0]
    pae_n = sorted(paes, key=lambda n: ("model_0" not in n and "sample_0" not in n, n))[0]
    with tempfile.TemporaryDirectory() as d:
        for n, b in files.items():
            open(os.path.join(d, os.path.basename(n)), "wb").write(b)
        p = subprocess.run([sys.executable, "-I", ipsae_py, os.path.join(d, os.path.basename(pae_n)),
                            os.path.join(d, os.path.basename(cif)), str(pae), str(dist)],
                           capture_output=True, text=True, cwd=d)
        txt = glob.glob(os.path.join(d, "*_%02d_%02d.txt" % (pae, dist)))
        txt = [t for t in txt if not t.endswith("_byres.txt")]
        if not txt:
            return {"error": "ipsae.py failed", "stderr": (p.stderr or p.stdout)[-500:]}
        rows = {}
        for line in open(txt[0]):
            f = line.split()
            if len(f) >= 12 and f[4] == "max":
                pair = tuple(sorted((f[0], f[1])))
                rows[pair] = {"ipsae": float(f[5]), "pdockq2": float(f[11]), "lis": float(f[12])}
        out = {}
        for t in targets:
            r = rows.get(tuple(sorted((binder, t))), {})
            out["ipsae_%s_%s" % (binder, t)] = r.get("ipsae")
            out["pdockq2_%s_%s" % (binder, t)] = r.get("pdockq2")
            out["lis_%s_%s" % (binder, t)] = r.get("lis")
        vals = [out["ipsae_%s_%s" % (binder, t)] for t in targets if out["ipsae_%s_%s" % (binder, t)] is not None]
        out["ipsae_best"] = max(vals) if vals else None
        out["ipsae_min"] = min(vals) if vals else None
        # contacts (heavy atoms within 4.5 A), UniProt numbering = CIF number + 120
        import gemmi
        st = gemmi.read_structure(os.path.join(d, os.path.basename(cif))); st.setup_entities()
        m = st[0]; ns = gemmi.NeighborSearch(m, st.cell, 5).populate()
        for t in targets:
            res = set()
            if binder in [c.name for c in m]:
                for r in m[binder]:
                    for a in r:
                        for mk in ns.find_atoms(a.pos, "\0", radius=4.5):
                            cra = mk.to_cra(m)
                            if cra.chain.name == t: res.add(cra.residue.seqid.num + 120)
            res = sorted(res)
            out["n_contact_res_" + t] = len(res)
            out["contact_res_" + t] = " ".join(map(str, res))
            dom = {}
            for u in res: dom[domain_of(u)] = dom.get(domain_of(u), 0) + 1
            out["domains_" + t] = ";".join("%s:%d" % kv for kv in sorted(dom.items()))
            out["apical_frac_" + t] = round(sum(1 for u in res if 189 <= u <= 383) / len(res), 2) if res else None
        nA, nB = out.get("n_contact_res_A", 0), out.get("n_contact_res_B", 0)
        out["binds_both_copies"] = bool(nA >= 5 and nB >= 5)
        out["structure_file"] = os.path.basename(cif); out["pae_file"] = os.path.basename(pae_n)
        return out

@app.function(image=image, timeout=900)
def score_remote(files, binder="C", targets=("A", "B"), pae=10, dist=10):
    return score_core(files, binder, tuple(targets), pae, dist)

def collect(job_dir):
    """Read every file of one downloaded job; unpack any tar.gz archive on the way."""
    files = {}
    for root, _, names in os.walk(job_dir):
        for n in names:
            p = os.path.join(root, n)
            if n.endswith((".tar.gz", ".tgz")):
                with tarfile.open(p) as tf:
                    for mem in tf.getmembers():
                        if mem.isfile() and mem.name.endswith((".cif", ".npz", ".json")):
                            files[mem.name.replace("/", "__")] = tf.extractfile(mem).read()
            elif n.endswith((".cif", ".npz", ".json")) and "job_request" not in n:
                files[os.path.relpath(p, job_dir).replace("\\", "__").replace("/", "__")] = open(p, "rb").read()
    return files

@app.local_entrypoint()
def main(folder: str, out: str, binder: str = "C"):
    jobs = sorted(d for d in glob.glob(os.path.join(folder, "[0-9][0-9]_*")) if os.path.isdir(d))
    print("job folders found:", len(jobs))
    payload = [(os.path.basename(j), collect(j)) for j in jobs]
    for name, f in payload:
        if not any(k.endswith(".npz") for k in f):
            print("  %s: NO PAE .npz found, files = %s" % (name, sorted(f)[:6]))
    results = list(score_remote.starmap([(f, binder) for _, f in payload]))
    rows = []
    for (name, _), r in zip(payload, results):
        rows.append({"rank": int(name[:2]), "job": name[3:], **r})
    cols = []
    for r in rows:
        for k in r:
            if k not in cols: cols.append(k)
    with open(out, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols); w.writeheader(); w.writerows(rows)
    print("wrote", out)
    for r in rows:
        print("rank %2d  ipSAE best %s  min %s  contacts A/B %s/%s  both=%s  %s" % (
            r["rank"], r.get("ipsae_best"), r.get("ipsae_min"), r.get("n_contact_res_A"), r.get("n_contact_res_B"),
            r.get("binds_both_copies"), r.get("error", "")))
