# Protein-3d-vids

Scripts that produce the PDFA x Ministry of Health Lassa fever antibody showcase video (30 s, 1080x1350, 20 fps):
the 8EJE glycoprotein trimer as a surface with each of the six chains in its own colour, and 10 de novo antibodies
(VH/VL) shown one after another on the same GP1/GP2 epitope, switching directly with no fade.

## Pipeline
| Step | Script | What it does |
|---|---|---|
| 0 | `scripts/convert_af.py` | AlphaFold Server CIF -> PDB |
| 1 | `scripts/dock3.py`, `scripts/sasa.py` | Restraint-guided rigid-body docking onto the exposed epitope (GP1 chain B 2-12, GP2 chain E 132-147); own Shrake-Rupley SASA |
| 2 | `scripts/prep2.py` | Align the trimer 3-fold axis to +y |
| 3 | `scripts/render.py` | PyMOL ray-traced frames: 3.6 s 360 deg intro spin, then 1.32 s per antibody, gentle camera sway |
| 4 | `scripts/overlay.py` | Pillow overlay (Inter font), ipTM labels, progress bar |
| 5 | `run_all.sh` | Runs everything, encodes with ffmpeg |

## Inputs (not included)
Put these in `inputs/`: `8EJE_boltz_ABCDEF.pdb` (chains A-C GP1, D-F GP2) and `lasv_pdbs/lasv_N_model_0.pdb`.
Also needed in the repo root: `iptm.json` ({"1": 0.87, ...}), used for the labels. The antibody designs are unpublished, so they are deliberately not committed.

## Requirements
`pip install pymol-open-source gemmi numpy scipy pillow`, ffmpeg, and the Inter font at `/usr/share/fonts/opentype/inter/`.
Rendering takes about 50 minutes for 600 frames.

## Caveats
Antibody poses are restraint-docked, not predicted complexes. The ipTM shown is the VH-VL interface value from AlphaFold Server, not antibody-target confidence.
Target chain colours were chosen to stay clear of the antibody colours (`scripts/pal.py`).
