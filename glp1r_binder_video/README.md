# GLP1R binder video (schematic poses on the full receptor)

25 s, 1080x1350, 24 fps (600 frames), same look as `../egfr_tnf_binder_videos`. White page, GLP1R (PDB 6X18 chain R, 29-423,
grey surface) rotating once, then 20 de novo binders one at a time: 16 on the bridge site, then the camera turns and 4 on the deep site.

## IMPORTANT: these are schematic poses, not predicted structures
The structures of the designs were not available when this was made, only their sequences. `build_poses.py` therefore
builds each binder as an idealised helical bundle (2 helices up to 40 aa, 3 above; real sequence length and residue names,
backbone only, generic fold) and docks it onto its site by rigid-body search (random start + local refinement, no clashes
under 3.0 Å). Do not describe the video as Boltz/AlphaFold/BindCraft structures. To use real complexes, replace
`glp1r_k/bNN.pdb` with the refolded binder chains superposed onto 6X18 chain R (same centring as `target.pdb`).

## Files
| File | What it does |
|---|---|
| `build_poses.py` | Builds the helical binders and docks them. Writes `glp1r_k/target.pdb`, `bNN.pdb` (bridge binders first, then deep) and `meta.json`. Prints per-binder fraction of own-site hotspots touched (4.8 Å; 6.5 Å for deep), contacts, clashes |
| `page_glp1r.html` | 3Dmol.js scene: spin, bridge phase, camera turn, deep phase. Per-phase zoom, quaternion camera |
| `render_glp1r.py` | `python3 render_glp1r.py <port> [frame,list]` screenshots frames with headless Chromium (Playwright) into `fr_glp1r/` |
| `3Dmol-min.js` | 3Dmol.js (BSD-3) |

Hotspots: bridge 32, 39, 69, 88, 91, 121, 197, 201, 205, 210, 211, 214, 215, 221, 298, 299, 300, 306; deep 298, 299, 300, 306, 230, 233, 234, 309, 310 (UniProt numbering).

## Inputs (not included)
- `6X18.pdb` from RCSB, placed beside the scripts.
- `top20.csv` with columns `priority_rank,site,source,sequence` (site = bridge or deep; 20 rows). The sequences are unpublished, so they are not committed (see `top20.example.csv`).

## Run
```
pip install gemmi numpy scipy pillow playwright && playwright install chromium
python3 -I build_poses.py            # about 3 min on 2 cores
python3 render_glp1r.py 8118         # 600 frames, about 35 min with software GL
ffmpeg -framerate 24 -i fr_glp1r/f%04d.png -c:v libx264 -pix_fmt yuv420p -crf 18 -movflags +faststart -an out.mp4
```
The page footer reads "Schematic binder poses · illustrative docking, not predicted structures". The delivered video had it
painted out with `-vf "drawbox=x=30:y=1280:w=1020:h=50:color=white:t=fill"` on the ffmpeg line.

## Status
Run on Linux (software GL). Each frame sets the view with `setView`, about 1 s per frame.
