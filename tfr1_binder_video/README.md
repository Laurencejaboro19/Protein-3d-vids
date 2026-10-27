# TfR1 binder video: 20 designs as Boltz-2.1 predicted complexes

25 s, 1080x1350, 24 fps (600 frames), no sound. White page, human TfR1 apical domain (grey surface), one binder at a time in submission order (rank 1 to 20), each in its own colour. The camera turns to face the binder; the bottom-left counter reads `Binder N of 20 · de novo, <BindCraft2|RFD4-Proteina>` with ipTM, ipSAE and predicted pH release from the submission table. Same renderer as the GLP1R video (`../glp1r_binder_video/`).

## What the structures are
Each binder is shown in its own hosted Boltz-2.1 refold: target chain A (human apical domain, 193 residues, UniProt 191-383) plus binder chain B, binder without an MSA, target with the automatic MSA, 1 sample, default settings. Nothing is docked by hand. `build_tfr1.py` only moves each complex into the rank-1 target frame by superposing the target C-alpha atoms (3 rounds of dropping the 25% most deviant residues). The domain core is the same in all 20 (core RMSD 0.14 to 0.22 A); only loops and termini differ (all-CA RMSD up to about 6 A), so each complex keeps its own grey surface. Scores in the video come from the submission screen, the shapes from these refolds, so they can differ.

## What each file does
| File | What it does | Worked |
|---|---|---|
| `powershell/01_boltz_install_and_login.ps1` | Installs the Boltz command-line tool and signs you in through the browser | Yes (Windows) |
| `powershell/02_download_boltz_results_and_zip.ps1` | Downloads the 20 finished jobs, finds the `.cif` files (20 of 20), copies them to `rank01.cif` ... `rank20.cif` and zips them | Yes (Windows) |
| `analyze_tfr1.py` | Per complex: checks target and binder sequences against `top20.csv`, fit RMSD, closest heavy-atom pair, interface sizes, design hotspots touched at 4.5 A | Yes (Linux) |
| `build_tfr1.py` | Writes `tfr1_bz/rNN.pdb` (target), `bNN.pdb` (binder) and `meta.json` | Yes (Linux) |
| `page_tfr1.html` | 3Dmol.js scene: one surface per complex, binder fades in and out per slot, camera angle per binder, counter and scores | Yes (checked by eye) |
| `render_tfr1.py` | `python3 render_tfr1.py <port>` screenshots 600 frames (Playwright, headless Chromium, software GL) into `fr_tfr1/` | Yes (about 15 min) |
| `3Dmol-min.js` | 3Dmol.js (BSD-3) | |

## Inputs (not included: the designs are unpublished)
- `bz/rank01.cif` ... `bz/rank20.cif` from `powershell/02_download_boltz_results_and_zip.ps1`.
- `top20.csv` with columns `rank_preference,name,sequence,ph_fold_release_x_human,iptm_human,ipsae_human` (see `top20.example.csv`). Names starting `BC2` are labelled BindCraft2, the rest RFD4-Proteina.
- `hotspots.txt`: your design hotspot residue numbers (UniProt), comma-separated, used only by `analyze_tfr1.py`.
- The Boltz jobs themselves were started from the Boltz-2.1 structure-and-binding endpoint (about $0.025 each, $0.50 for 20); put the 20 prediction ids in script 02.

## Run
```
# Windows PowerShell: 01 once, then 02 (put your 20 job ids in it); unzip the cifs into bz/
pip install gemmi numpy scipy pillow playwright && playwright install chromium
python3 -I analyze_tfr1.py
python3 -I build_tfr1.py
python3 render_tfr1.py 8123        # 600 frames, about 15 min with software GL
ffmpeg -framerate 24 -i fr_tfr1/f%04d.png -c:v libx264 -pix_fmt yuv420p -crf 18 -movflags +faststart -an out.mp4
```

## Caveats
- All 20 refolds matched the submitted sequences. No heavy-atom pair is closer than 2.4 A.
- In the Boltz-2.1 refolds four binders touch fewer of the five design hotspots than the submission screen recorded, so the video can show them on a different part of the domain than designed.
- The target is a monomer crop of the apical domain, the same crop used for scoring, not the TfR1 dimer.
- These are predictions, not experiments.
