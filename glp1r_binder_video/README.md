# GLP1R binder video: 20 designs as Boltz-2.1 predicted complexes

25 s, 1080x1350, 24 fps (600 frames), no sound. White page, GLP1R surface (grey), one binder at a time in the order of the submission
(rank 1 to 20). Each binder fades in and out inside its own time slot, the camera turns to face the binder, and the bottom-left counter
reads `Binder N of 20 · de novo, <bridge|deep> site` with the ipTM and ipSAE from the submission CSV. Every binder has its own colour.

## What the structures are
Each binder is shown in its own Boltz-2.1 refold (receptor chain A + binder chain B, full GLP1R 24-432). Nothing is docked by hand.
`build_boltz_complexes.py` only moves each complex into one common frame (the PDB 6X18 receptor frame) by superposing the receptor
C-alpha atoms of the transmembrane core (residues 145-390). The 20 Boltz receptors are not identical (TM-core RMSD to 6X18 is 1.8 to
4.3 A; some have the ECD tilted differently), so the grey receptor changes slightly from one binder to the next. The page swaps the
receptor only while no binder is visible. Tried and rejected: putting all 20 binders on one fixed 6X18 receptor. They kept only about
4-36% of the contacts Boltz predicted, so it would show binding that is not real.
Scores in the video come from the submission screen (mostly Boltz-2.2.1), the shapes from the Boltz-2.1 refolds, so ipTM can differ a little.

## What each file does
| File | What it does |
|---|---|
| `powershell/01_boltz_install_and_login.ps1` | Installs the Boltz command-line tool (`boltz-api`) and signs you in through your browser. Worked on Windows. |
| `powershell/02_download_boltz_results.ps1` | `boltz-api download-results` for each of the 20 job ids, then zips everything and counts the `.cif` files (20 of 20 when it works). |
| `powershell/03_collect_cifs.ps1` | Copies only the 20 `.cif` files into `rank01.cif` ... `rank20.cif` and zips them (small enough to upload). |
| `analyze_boltz.py` | For each complex: checks the binder sequence against the CSV, counts receptor residues within 4.5 A, bridge and deep hotspots touched, overlap with the GLP-1 footprint (6X18 chain P), TM-core RMSD to 6X18. Prints one line per design. |
| `build_boltz_complexes.py` | Superposes each complex onto 6X18 (TM core), writes `glp1r_bz/rNN.pdb` (receptor), `bNN.pdb` (binder) and `meta.json` (ranks, sites, binder centroids, receptor axis, ipTM, ipSAE). |
| `page_glp1r.html` | 3Dmol.js scene: receptor vertical, one surface per complex (only the active one shown), binder cartoon fades in and out per slot, camera angle per binder from the binder centroid, counter and scores. |
| `render_glp1r.py` | `python3 render_glp1r.py <port> [frame,list]` screenshots the page frame by frame (Playwright, headless Chromium) into `fr_glp1r/`. |
| `3Dmol-min.js` | 3Dmol.js (BSD-3). |
| `legacy_rigid_docking/` | Earlier version: rigid AlphaFold monomers placed by random search on 6X18. They ran, but the poses are not predicted complexes and the deep binders could not reach the deep pocket (overlaps or outside placement). Kept for reference only. |

## Inputs (not included)
- `6X18.pdb` from RCSB, next to the scripts.
- `top20.csv` with columns `priority_rank,site,source,sequence,iptm,ipsae` (sequences are unpublished; see `top20.example.csv`).
- `bz/rank01.cif` ... `bz/rank20.cif` from `powershell/03_collect_cifs.ps1`.

## Run
```
# Windows PowerShell: 01, then 02 (put your 20 job ids in it), then 03; unzip the cifs into bz/
pip install gemmi numpy scipy pillow playwright && playwright install chromium
python3 -I analyze_boltz.py
python3 -I build_boltz_complexes.py
python3 render_glp1r.py 8123        # 600 frames, about 20 min with software GL
ffmpeg -framerate 24 -i fr_glp1r/f%04d.png -c:v libx264 -pix_fmt yuv420p -crf 18 -movflags +faststart -an out.mp4
```
Checked by eye on Linux (software GL). The PowerShell scripts were run on Windows by the author; the ids are placeholders in script 02.

## Reading the results (from this run)
Every Boltz complex has no heavy-atom pair closer than 2.4 A. Bridge-site designs touch 7 to 15 of the 18 bridge hotspots; the four
deep-site designs touch 3 to 5 of the 9 deep hotspots at 4.5 A and also sit on the ECD and upper cleft. Two bridge-designed binders
(ranks 5 and 19) reach 8 of 9 deep hotspots. These are predictions, not experiments.

## Two more styles (same data, same 25 s timeline)
Both use the grey cartoon receptor (one receptor per complex, swapped while that binder is shown) with the binder as a coloured cartoon.
| Style | Page | Render | Output |
|---|---|---|---|
| Dark, 1920x1080, right-hand info panel (rank, method, site, length, hotspots touched, ipSAE / ipTM / binder pLDDT) | `page_dark.html` | `python3 render_dark.py <port>` | `fr_dark/` |
| White, 1080x1350, same header and fonts as the first version, text line with method, site, length, scores, hotspots | `page_white.html` | `python3 render_white.py <port>` | `fr_white/` |

`build_boltz_complexes.py` now also writes `src`, `len`, `plddt`, `hit`, `tot` into `meta.json`, so `top20.csv` needs the columns
`priority_rank,site,source,sequence,length,iptm,ipsae,plddt,hotspots_hit,hotspots_total` (`plddt` as 0 to 1; see `top20.example.csv`).
Encode with the same ffmpeg line, e.g. `ffmpeg -framerate 24 -i fr_dark/f%04d.png -c:v libx264 -pix_fmt yuv420p -crf 18 -movflags +faststart -an dark.mp4`.
Run each render as one foreground command (or a properly detached job) and give it a free port; a render started from a shell that then exits stops partway.
The dark layout was inspired by another participant's GLP1R video; nothing was copied from it.
