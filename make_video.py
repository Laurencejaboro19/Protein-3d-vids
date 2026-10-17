#!/usr/bin/env python3
"""
make_video.py - one-command Windows/PowerShell (and Linux/macOS) builder for the
Lassa fever antibody showcase video, using the scripts already in ./scripts (unchanged).

Pipeline: SASA -> dock -> prep -> PyMOL frames (parallel) -> Pillow overlay -> ffmpeg MP4.

Example (PowerShell, from the repo root):
  python make_video.py --target C:\\data\\8EJE_boltz_ABCDEF.pdb --designs C:\\data\\lasv_pdbs --iptm C:\\data\\iptm.json

Quick look before the long render (3 frames, no video):
  python make_video.py --target ... --designs ... --iptm ... --preview

Re-running skips finished steps and frames, so an interrupted render can be resumed.
"""
import argparse, glob, importlib.util, json, os, re, shutil, subprocess, sys, time, urllib.request, zipfile

ROOT = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.join(ROOT, "scripts")
NAB = 10
TOTAL_FRAMES = 600          # 30 s at 20 fps (fixed by the scripts)
PREVIEW_FRAMES = [0, 90, 244]


def log(msg):
    print(f"[make_video] {msg}", flush=True)


def die(msg):
    print(f"\n[make_video] ERROR: {msg}\n", file=sys.stderr)
    sys.exit(1)


def run(cmd, cwd, what):
    log(what)
    r = subprocess.run(cmd, cwd=cwd)
    if r.returncode != 0:
        die(f"step failed: {what} (exit {r.returncode})")


def check_deps():
    missing = [m for m in ("pymol", "gemmi", "numpy", "scipy", "PIL") if importlib.util.find_spec(m) is None]
    if missing:
        die("missing Python packages: " + ", ".join(missing) + "\n"
            "Easiest on Windows is conda (PyMOL has no reliable plain-pip wheel there):\n"
            "  conda create -n pdfa -c conda-forge python=3.11 pymol-open-source gemmi numpy scipy pillow ffmpeg\n"
            "  conda activate pdfa")
    if shutil.which("ffmpeg") is None:
        die("ffmpeg not found on PATH. Install it with:  conda install -c conda-forge ffmpeg   (or winget install ffmpeg)")


def to_pdb(src_dir, n, dst):
    """Find design n's model_0 as PDB, or convert a CIF from AlphaFold Server."""
    for pat in (f"lasv_{n}_model_0.pdb", f"fold_lasv_{n}_model_0.pdb"):
        p = os.path.join(src_dir, pat)
        if os.path.exists(p):
            shutil.copy(p, dst); return
    cifs = glob.glob(os.path.join(src_dir, "**", f"*lasv_{n}_model_0.cif"), recursive=True)
    if cifs:
        import gemmi
        st = gemmi.read_structure(cifs[0]); st.setup_entities(); st.write_pdb(dst); return
    die(f"design {n} not found in {src_dir}: expected lasv_{n}_model_0.pdb (or a .cif of the same name)")


def find_fonts(build, font_dir):
    """Return a directory containing Inter-Bold.otf and Inter-Medium.otf, or None."""
    need = ("Inter-Bold.otf", "Inter-Medium.otf")
    cands = [font_dir] if font_dir else []
    cands += [os.path.join(ROOT, "fonts"), os.path.join(build, "fonts"), "/usr/share/fonts/opentype/inter"]
    for d in cands:
        if d and all(os.path.exists(os.path.join(d, f)) for f in need):
            return d
    dst = os.path.join(build, "fonts")
    try:
        log("downloading the Inter font (once) ...")
        os.makedirs(dst, exist_ok=True)
        zp = os.path.join(dst, "inter.zip")
        urllib.request.urlretrieve("https://github.com/rsms/inter/releases/download/v4.0/Inter-4.0.zip", zp)
        with zipfile.ZipFile(zp) as z:
            for name in z.namelist():
                if name.endswith(need) and "/otf/" in name.replace("\\", "/") and "Italic" not in name:
                    with z.open(name) as s, open(os.path.join(dst, os.path.basename(name)), "wb") as o:
                        shutil.copyfileobj(s, o)
        if all(os.path.exists(os.path.join(dst, f)) for f in need):
            return dst
    except Exception as e:
        log(f"font download failed ({e}); falling back to a system font")
    return None


def patch_overlay(build, font_dir):
    """Write build/overlay_run.py = scripts/overlay.py with only the font lookup made portable."""
    src = open(os.path.join(SCRIPTS, "overlay.py"), encoding="utf-8").read()
    fd = find_fonts(build, font_dir)
    if fd:
        repl = f"F=lambda n,s: ImageFont.truetype(os.path.join({fd!r},n+'.otf'),s)"
    else:
        win = os.environ.get("WINDIR", r"C:\Windows") + r"\Fonts"
        cands = [os.path.join(win, "arialbd.ttf"), os.path.join(win, "arial.ttf"),
                 "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]
        repl = ("F=lambda n,s: ImageFont.truetype(next(p for p in %r if os.path.exists(p) and "
                "(('Bold' in n)==(('bd' in os.path.basename(p).lower()) or ('Bold' in p)))) ,s)" % (cands,))
    new, k = re.subn(r"^F=lambda n,s:.*$", lambda m: repl, src, count=1, flags=re.M)
    if k != 1:
        die("could not find the font line in scripts/overlay.py (has it changed?)")
    out = os.path.join(build, "overlay_run.py")
    open(out, "w", encoding="utf-8").write(new)
    return out


def render_frames(build, frames, workers):
    todo = [f for f in frames if not os.path.exists(os.path.join(build, "frames", f"f{f:04d}.png"))]
    if not todo:
        log("all requested frames already rendered - skipping"); return
    workers = max(1, min(workers, len(todo)))
    chunks = [todo[i::workers] for i in range(workers)]   # interleave so workers finish together
    log(f"rendering {len(todo)} frames with {workers} PyMOL worker(s) (about 5 s/frame/worker at 1080x1350)")
    procs = []
    for c in chunks:
        procs.append(subprocess.Popen([sys.executable, os.path.join(SCRIPTS, "render.py"), "0", "0", "0",
                                       ",".join(map(str, c))], cwd=build))
    t0 = time.time()
    while any(p.poll() is None for p in procs):
        done = sum(os.path.exists(os.path.join(build, "frames", f"f{f:04d}.png")) for f in todo)
        print(f"\r[make_video] frames {done}/{len(todo)}  {time.time()-t0:5.0f}s", end="", flush=True)
        time.sleep(3)
    print()
    if any(p.returncode for p in procs):
        die("a render worker failed - re-run the same command to resume")


def main():
    ap = argparse.ArgumentParser(description="Build the Lassa antibody showcase video from the repo scripts.")
    ap.add_argument("--target", required=True, help="Boltz target PDB (chains A-C GP1, D-F GP2), e.g. 8EJE_boltz_ABCDEF.pdb")
    ap.add_argument("--designs", required=True, help="folder with lasv_1_model_0.pdb ... lasv_10_model_0.pdb (CIFs also accepted)")
    ap.add_argument("--iptm", required=True, help='iptm.json like {"1": 0.87, ..., "10": 0.91}')
    ap.add_argument("--out", default="lassa_antibodies.mp4", help="output MP4 name (default %(default)s)")
    ap.add_argument("--build", default=os.path.join(ROOT, "build"), help="working folder (default ./build)")
    ap.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) // 2), help="parallel PyMOL renderers")
    ap.add_argument("--font-dir", default=None, help="folder with Inter-Bold.otf and Inter-Medium.otf (auto-downloaded if absent)")
    ap.add_argument("--preview", action="store_true", help="render only 3 frames, write build/preview.png, no video")
    ap.add_argument("--redock", action="store_true", help="redo docking even if poses already exist")
    a = ap.parse_args()

    check_deps()
    for p in (a.target, a.designs, a.iptm):
        if not os.path.exists(p):
            die(f"not found: {p}")
    ip = json.load(open(a.iptm))
    miss = [str(i) for i in range(1, NAB + 1) if str(i) not in ip]
    if miss:
        die("iptm.json is missing keys: " + ", ".join(miss))

    build = os.path.abspath(a.build)
    os.makedirs(os.path.join(build, "inputs", "lasv_pdbs"), exist_ok=True)
    os.makedirs(os.path.join(build, "frames"), exist_ok=True)
    os.makedirs(os.path.join(build, "out"), exist_ok=True)
    shutil.copy(a.target, os.path.join(build, "inputs", "8EJE_boltz_ABCDEF.pdb"))
    shutil.copy(a.iptm, os.path.join(build, "iptm.json"))
    for n in range(1, NAB + 1):
        to_pdb(a.designs, n, os.path.join(build, "inputs", "lasv_pdbs", f"lasv_{n}_model_0.pdb"))
    py = sys.executable

    if not os.path.exists(os.path.join(build, "tgt_sasa.npy")):
        run([py, os.path.join(SCRIPTS, "sasa.py")], build, "step 1/5  surface accessibility of the target (a few minutes)")
    if a.redock or not all(os.path.exists(os.path.join(build, f"ab{n}_docked.pdb")) for n in range(1, NAB + 1)):
        run([py, os.path.join(SCRIPTS, "dock3.py"), ",".join(map(str, range(1, NAB + 1)))], build,
            "step 2/5  docking the 10 antibodies on the epitope (several minutes)")
    if a.redock or not os.path.exists(os.path.join(build, "target_prep.pdb")):
        run([py, os.path.join(SCRIPTS, "prep2.py")], build, "step 3/5  aligning the trimer axis")

    frames = PREVIEW_FRAMES if a.preview else list(range(TOTAL_FRAMES))
    log("step 4/5  rendering 3D frames")
    render_frames(build, frames, a.workers)

    overlay = patch_overlay(build, a.font_dir)
    for f in frames:
        run([py, overlay, str(f), str(f + 1)], build, f"overlay frame {f}") if a.preview else None
    if a.preview:
        from PIL import Image
        ims = [Image.open(os.path.join(build, "out", f"f{f:04d}.png")).resize((540, 675)) for f in frames]
        m = Image.new("RGB", (540 * len(ims), 675), "white")
        for i, im in enumerate(ims): m.paste(im, (540 * i, 0))
        pv = os.path.join(build, "preview.png"); m.save(pv)
        log(f"preview written: {pv}"); return
    run([py, overlay, "0", str(TOTAL_FRAMES)], build, "adding titles, ipTM labels and progress bar")

    outp = os.path.abspath(a.out)
    run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", "20", "-i", os.path.join(build, "out", "f%04d.png"),
         "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", "-preset", "medium", "-movflags", "+faststart", outp],
        build, "step 5/5  encoding MP4")
    log(f"DONE -> {outp}")


if __name__ == "__main__":
    main()
