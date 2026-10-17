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

## Status: UNTESTED ON WINDOWS
The scripts were tested on Linux (structure prep, filtering, and a 3-frame render). The PowerShell blocks below were
written for Windows but have not been run there. If a block shows something different from "You should see", send the
error text and fix that block.

## Run it in PowerShell (paste one block at a time, in order)

### Block 1. Check Python and install ffmpeg
What: confirms Python 3.10+ and installs ffmpeg. Why: Python runs every script, ffmpeg turns the frames into the mp4.
```powershell
python --version
winget install --id Gyan.FFmpeg -e
```
You should see `Python 3.10` or higher, then winget saying it installed (or "already installed"). Close and reopen PowerShell afterwards so `ffmpeg` is found. Check with `ffmpeg -version`, which should print a version line.

### Block 2. Get the repo
What: downloads the code and moves into the video folder. Why: all scripts use paths relative to this folder.
```powershell
git clone https://github.com/Laurencejaboro19/Protein-3d-vids.git
cd Protein-3d-vids\egfr_tnf_binder_videos
dir
```
You should see `prep.py`, `filt.py`, `page_seq.html`, `render_seq.py`, `3Dmol-min.js`, `README.md`.

### Block 3. Install the Python packages and the browser
What: installs gemmi, numpy, scipy, playwright, then downloads Chromium. Why: gemmi/numpy/scipy do the structure maths; Playwright drives Chromium to draw each frame.
```powershell
python -m pip install gemmi numpy scipy playwright
python -m playwright install chromium
```
You should see `Successfully installed ...`, then a Chromium download progress bar ending without errors.

### Block 4. Put your complex structures in place
What: copies your predicted complexes beside the scripts. Why: the scripts read them from `egfr_src` and `tnf_src`; they are not in the repo because they are design data. Change the two source paths to where your folders are.
```powershell
New-Item -ItemType Directory -Force egfr_src, tnf_src | Out-Null
Copy-Item -Recurse "C:\path\to\egfr_h409_night1_winners" egfr_src\
Copy-Item -Recurse "C:\path\to\submission_track1_40" tnf_src\
(Get-ChildItem egfr_src -Recurse -Filter human_complex.cif).Count
(Get-ChildItem tnf_src -Recurse -Filter *_human.cif).Count
```
You should see `21` and then `40`. EGFR files must be named `human_complex.cif` inside `egfr_src\egfr_h409_night1_winners\structures\<name>\`, TNF files `*_r<N>_human.cif` inside `tnf_src\<folder>\structures\`.

### Block 5. Prepare the structures
What: superposes all complexes onto the first, maps TNF binders into one groove using the trimer's 3-fold symmetry, rotates the scene to face the binding site. Why: so every binder lands in the same place on screen.
```powershell
python prep.py
```
You should see `egfr 21 binders; centroid dist ...`, `C3 check A->B then B->C rmsd` (about 0.2), `symmetry copy used per binder [...]`, `tnf 40 binders; ...`. Folders `egfr` and `tnf` appear.

### Block 6. Filter bad poses
What: drops binders that clash with the target or sit off the shared site. Why: a clean one-at-a-time sequence.
```powershell
python filt.py
```
You should see `egfr kept 21 of 21 dropped idx []` and `tnf kept 28 of 40 dropped idx [3, 4, 5, 6, 8, 15, 20, 24, 26, 28, 30, 31]`. Folders `egfr_k` and `tnf_k` appear.

### Block 7. Quick test render (3 frames, optional)
What: renders only frames 0, 200 and 400 of TNF. Why: confirms Chromium and the scene work before the long run. It still steps through all 600 frames, so it can take several minutes.
```powershell
python render_seq.py tnf 8102 0,200,400
dir fr_tnf_seq
```
You should see progress lines `tnf 0`, `tnf 100` ... `tnf 500` and three PNGs. Open `fr_tnf_seq\f0400.png`: white page, grey TNF surface, one coloured binder, "Binder N of 28".

### Block 8. Render all frames
What: renders 600 frames per target, one window each. Why: this is the long step (software rendering, roughly an hour each). Starting both at once uses two CPU cores.
```powershell
Start-Process powershell -ArgumentList "-NoExit","-Command","cd '$PWD'; python render_seq.py egfr 8101"
Start-Process powershell -ArgumentList "-NoExit","-Command","cd '$PWD'; python render_seq.py tnf 8102"
```
Two new windows open, each printing `egfr 0`, `egfr 100` ... `egfr 500` (and `tnf ...`). Check the count any time:
```powershell
(Get-ChildItem fr_egfr_seq).Count
(Get-ChildItem fr_tnf_seq).Count
```
You should see both reach `600`.

### Block 9. Encode the videos
What: joins the frames into mp4 files. Why: gives you the two ready-to-post videos (25 s, 24 fps).
```powershell
ffmpeg -framerate 24 -i fr_egfr_seq/f%04d.png -c:v libx264 -pix_fmt yuv420p -crf 18 -movflags +faststart PDFA_EGFR_binders_one_at_a_time_25s.mp4
ffmpeg -framerate 24 -i fr_tnf_seq/f%04d.png -c:v libx264 -pix_fmt yuv420p -crf 18 -movflags +faststart PDFA_TNF_alpha_binders_one_at_a_time_25s.mp4
dir *.mp4
```
You should see ffmpeg count up to `frame= 600`, then two `.mp4` files in the listing.

## Notes
- Edit the heading, subtitle and zoom per target in the `CFG` block inside `page_seq.html`.
- Timing constants (`N`, `P1`, `START`, `END`, `FADE`) are at the top of the script in `page_seq.html`.
- Poses are Boltz-2 predicted complexes, computational only.
- If `python` is not found, use `py` instead.
