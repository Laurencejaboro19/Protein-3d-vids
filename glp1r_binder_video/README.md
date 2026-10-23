# GLP1R binder video (20 AlphaFold binders docked on the full receptor)

25 s, 1080x1350, 24 fps (600 frames), same look as `../egfr_tnf_binder_videos`. White page, GLP1R (PDB 6X18 chain R, 29-423,
grey surface) with its long axis vertical for the whole video: one spin, then 16 bridge-site binders one at a time, the camera turns
about the vertical axis, then 4 deep-site binders. Every binder has its own colour (20-colour palette in `page_glp1r.html`).

## What the poses are (read this)
Each binder is the real AlphaFold Server fold (model 0, binder alone). The pose on the receptor is NOT a predicted complex:
`build_poses_af.py` places each rigid binder by random search + local refinement. Score = soft closeness to the hotspot residues
of its designed site + interface size - clashes (no heavy-atom pair under 3.0 Å, at least 25 atoms within 4.8 Å).
`verify_poses.py` re-reads the written PDBs and checks sequence = submitted sequence, site = designed site, clashes, contact size.
Typical result: every binder touches the receptor (13-47 atoms within 4.5 Å), bridge binders touch 1-5 of 18 bridge hotspots at 4.5 Å,
deep binders sit at the mouth of the deep pocket (0-1 of 9 hotspots at 4.5 Å, 1-3 at 6.5 Å) because the pocket is buried in the
helix bundle. Do not describe the video as predicted complexes. `build_poses_schematic.py` is the older version that builds idealised
helices from sequence alone (no structures needed).

## Files
| File | What it does |
|---|---|
| `build_poses_af.py` | Reads `af/fold_gN/*_model_0.cif` (N = submission rank), docks, writes `glp1r_k/target.pdb`, `bNN.pdb`, `meta.json` (incl. the receptor's long axis) |
| `verify_poses.py` | Independent check table of the written poses |
| `page_glp1r.html` | 3Dmol.js scene, vertical receptor, camera turns only about the vertical axis |
| `render_glp1r.py` | `python3 render_glp1r.py <port> [frame,list]` screenshots frames with headless Chromium (Playwright) into `fr_glp1r/` |
| `3Dmol-min.js` | 3Dmol.js (BSD-3) |

## Inputs (not included)
- `6X18.pdb` from RCSB beside the scripts.
- `top20.csv` with `priority_rank,site,source,sequence` (site = bridge or deep). The sequences are unpublished (see `top20.example.csv`).
- `af/fold_gN/` unzipped AlphaFold Server results, one per rank.

## Run
```
pip install gemmi numpy scipy pillow playwright && playwright install chromium
python3 -I build_poses_af.py     # about 6 min on 2 cores
python3 -I verify_poses.py
python3 render_glp1r.py 8123     # 600 frames, about 35 min with software GL
ffmpeg -framerate 24 -i fr_glp1r/f%04d.png -c:v libx264 -pix_fmt yuv420p -crf 18 -movflags +faststart -an out.mp4
```
The page footer is empty. Frames were checked by eye on Linux (software GL).
