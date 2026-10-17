# EGFR and TNF-α binder videos (white background, one binder at a time)

25 s, 1080x1350, 24 fps (600 frames). A white page with the target as a grey surface, rotating once, then each
designed binder appears on the same site, fades out, and the next one fades in. Heading: "Protein Design for Africa".
This is separate from the Lassa pipeline in the repo root; nothing there is touched.

## What is here
| File | What it does |
|---|---|
| `prep.py` | Superposes every predicted complex onto the first one (Kabsch on target CA atoms), maps TNF binders into one groove using the trimer's 3-fold symmetry, rotates the scene so the binding site faces the camera. Writes `egfr/` and `tnf/` |
| `filt.py` | Drops binders that clash with the target (closest CA to target CA < 3.5 Å) or sit off the shared site (centroid > 14 Å from median). Writes `egfr_k/` (21 of 21 kept) and `tnf_k/` (28 of 40 kept) |
| `page_seq.html` | The scene (3Dmol.js): one binder at a time. `page.html` is the older version where binders stack up |
| `render_seq.py` / `render.py` | Headless Chromium (Playwright) loads the page, calls `render(i)` for every frame and screenshots it |
| `3Dmol-min.js` | 3Dmol.js (BSD-3), bundled so rendering works offline |

## Inputs (not included)
The designed complexes are unpublished or submission data, so they are not committed. Put them here, beside the scripts:
- `egfr_src/egfr_h409_night1_winners/structures/*/human_complex.cif` (target chain A, binder chain B)
- `tnf_src/<any_folder>/structures/*_r<N>_human.cif` (target chains A, B, C, binder chain D)

## Requirements
Python 3.10+, ffmpeg. Install the Python packages and the browser:
```powershell
pip install gemmi numpy scipy playwright
playwright install chromium
```
You should see pip finish with "Successfully installed", then Chromium download.

## Steps (PowerShell, run inside this folder)
**1. Prepare the structures.** Aligns, symmetry-maps and orients them.
```powershell
python prep.py
```
You should see: `egfr 21 binders`, then `C3 check ... rmsd` (about 0.2), then `tnf 40 binders`. New folders `egfr/` and `tnf/` appear.

**2. Filter bad poses.**
```powershell
python filt.py
```
You should see: `egfr kept 21 of 21` and `tnf kept 28 of 40`. New folders `egfr_k/` and `tnf_k/` appear.

**3. Render the frames.** One command per target, each takes a long time on CPU software rendering (roughly an hour). Run them in two windows if you like.
```powershell
python render_seq.py egfr 8101
python render_seq.py tnf 8102
```
You should see progress lines `egfr 0`, `egfr 100` ... up to 500. Frames land in `fr_egfr_seq/` and `fr_tnf_seq/` (`f0000.png` to `f0599.png`).
Quick test of only a few frames: `python render_seq.py tnf 8102 0,200,400` (it still steps through all 600, but saves just those).

**4. Encode the video.**
```powershell
ffmpeg -framerate 24 -i fr_egfr_seq/f%04d.png -c:v libx264 -pix_fmt yuv420p -crf 18 -movflags +faststart PDFA_EGFR_binders_one_at_a_time_25s.mp4
ffmpeg -framerate 24 -i fr_tnf_seq/f%04d.png -c:v libx264 -pix_fmt yuv420p -crf 18 -movflags +faststart PDFA_TNF_alpha_binders_one_at_a_time_25s.mp4
```
You should see ffmpeg count up to frame=600 and two 25 s mp4 files.

## Notes
- Edit the heading, subtitle and zoom per target in the `CFG` block inside `page_seq.html`.
- Timing constants (`N`, `P1`, `START`, `END`, `FADE`) are at the top of the script in `page_seq.html`.
- Poses are Boltz-2 predicted complexes, computational only.
