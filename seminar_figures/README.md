# Seminar figures — image pipeline

Every picture used in *De Novo Protein Design in Medicine* (final-year
seminar, Chemistry, University of Benin, 2026) — both the slide deck and the
written report — together with the code that fetched, cleaned and
composited them, and the code that built the report itself.

Nothing here is hand-edited in an image editor. Running the scripts in order
reproduces all 17 figures from scratch.

## Order to run things

```powershell
# 1. structure images, straight from the RCSB Protein Data Bank
powershell -ExecutionPolicy Bypass -File powershell\get_pdb_images.ps1
#    -> %USERPROFILE%\Downloads\pdbpics\          + CITATIONS.txt

# 2. instrument photos, diagrams and graphical abstracts, from Wikimedia Commons
powershell -ExecutionPolicy Bypass -File powershell\get_graphical_abstracts.ps1
#    -> "%USERPROFILE%\Downloads\graphical abstract\"  + CITATIONS.txt
```

```bash
# 3. optional repairs on individual panels
python python/clean_images.py --trim    raw.png  trimmed.png
python python/clean_images.py --sharpen banner.png sharp.png --width 1500

# 4. composite the multi-panel plates
python python/make_plates.py --pdb   ~/Downloads/pdbpics \
                             --extra "~/Downloads/graphical abstract" \
                             --out   paperfig

# 5. build the report (optional — needs the chapter HTML files)
python python/build_two_pass.py
```

## What each script is for

| File | Does |
|---|---|
| `powershell/get_pdb_images.ps1` | Downloads one structure image per PDB entry and records the id, contents, experimental method and resolution of each. |
| `powershell/get_graphical_abstracts.ps1` | Downloads the non-PDB pictures through the Wikimedia Commons API, reading each file's real title, author and licence back out of the API so the credit lines are not written from memory. |
| `python/clean_images.py` | `--trim` crops letterboxed screenshots, `--sharpen` makes small text in a downloaded banner readable, `--flatten` composites transparency onto white. |
| `python/make_plates.py` | Composites single panels into the multi-panel figures, with labels that are measured before they are drawn. |
| `python/build_report.py` | Lays the report out directly with python-docx: Times New Roman 12pt, 1.5 spacing, justified, 1.5in left margin, roman front matter and arabic body in separate sections. |
| `python/make_toc.py` | Harvests the headings into a contents scaffold. |
| `python/build_two_pass.py` | Builds once to find which page each heading lands on, then rebuilds with the real page numbers written in. |
| `figure_manifest.csv` | Every figure: PDB id, contents, experimental method, resolution and source. |

## Two bugs worth knowing about

**PowerShell variable scope.** The first version of both download scripts did
`$cite += $line` inside the download function. PowerShell gives a function its
own copy of a variable from the calling scope, so every citation line appended
in there was discarded on return: 12 images downloaded, 2 citations recorded.
Both scripts now have the function *return* its line, and the caller appends it.

**Labels baked into images.** `make_plates.py` originally drew a descriptive
label under each panel. Those strings were wider than the panels, so adjacent
labels overlapped *inside the PNG* — invisible in the script, impossible to fix
from the document. Labels are now short, and the font is shrunk until every one
measurably fits inside its own panel before anything is drawn.

## Needs

`pip install -r requirements.txt` — Pillow, python-docx, beautifulsoup4, pypdf.
The report build also wants LibreOffice on PATH for the DOCX→PDF step.

## Licensing of the images

Structure images come from the RCSB Protein Data Bank (CC0). The rest are
Wikimedia Commons files under CC0, CC BY, CC BY-SA or public domain, or
figures credited to the paper they came from. `CITATIONS.txt`, written by the
download scripts, carries the author and licence for every file; the credit
lines under the figures in the report are taken from it.

## `figures/`

The 17 finished figures as they appear in the report, so they can be reused
without re-running the pipeline. `figure_manifest.csv` says what each one is.
