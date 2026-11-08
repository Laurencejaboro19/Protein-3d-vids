# KRAS G12D binder video (Adaptyv Challenge 5)

24 fps, 1080x1350, 25 s. The target (HLA-A*11:01 + b2m with the KRAS G12D peptide VVVGADGVGK in gold) is shown as a surface.
The 20 final binders appear one after another, each as its own Boltz-2.1 refold on the **G12D complex only**.
On screen for every binder: the three ipSAE values (G12D, WT, peptide-free HLA) from the Boltz-2 screening, plus length and tier.

Adapted from `../tfr1_binder_video`. Differences: target is HLA (chain A) + b2m (B) + peptide (C), binder is chain D; frames are aligned on HLA CA atoms;
one shared target model instead of one per binder; opaque target surface, camera tilted to look down into the groove so the gold peptide shows under each binder.

## Pipeline (what worked, in order)
| Step | File | Where | What it does |
|---|---|---|---|
| 1 | `powershell/01_boltz_install_and_login.ps1` | Windows PowerShell | installs the Boltz CLI, browser sign-in |
| 2 | `powershell/02_start_refolds.ps1` | Windows PowerShell | one Boltz-2.1 structure-and-binding job per binder (A HLA 276 aa, B b2m 99 aa, C peptide, D binder; msa empty for C and D) |
| 3 | `powershell/03_download_results_and_zip.ps1` | Windows PowerShell | `download-results` for each job, collects `rankNN.cif`, zips with the CSV |
| 4 | `build_kras.py` | Python (gemmi, numpy) | superposes HLA CA (3 rounds dropping the 25% most deviant), writes `t_hla.pdb`, `t_pep.pdb`, `bNN.pdb`, `meta.json` |
| 5 | `page_kras.html` + `render_kras.py` | Playwright + 3Dmol.js | frames `fr_kras/fNNNN.png` (~1 s per frame) |
| 6 | ffmpeg | | `ffmpeg -framerate 24 -i fr_kras/f%04d.png -c:v libx264 -pix_fmt yuv420p -crf 18 -movflags +faststart out.mp4` |
`powershell/04_make_video.ps1` runs steps 4-6 from the zip.

## Honest status
- Steps 3-6 were run for the delivered video (the zip came from the 20 refolds, 20 of 20 .cif found).
- The 20 refold jobs themselves were started through the Boltz connector in Claude with this exact input. `02_start_refolds.ps1` builds the same request for the CLI but was not run end to end; step 1 and 3 are the same CLI pattern as the TfR1 scripts.
- `04_make_video.ps1` is the Windows wrapper of the commands that ran on Linux; it was not run on Windows.
- Refolds are Boltz-2.1 predictions, not experiments. Ranks 6 and 19 sit further from the peptide in the refold (closest approach about 6.3 and 4.3 A, versus 1.9-3.5 A for the rest).
- ipSAE values come from the earlier Boltz-2 screening (WT and peptide-free columns are the max over the screen), not from these 20 refolds.

## Not in the repo
Sequences, the final-20 CSV, .cif files, frames and video are gitignored: the designs are unpublished. Keep this repo private.
