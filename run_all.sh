#!/usr/bin/env bash
# Full pipeline. Run from the repo root, with inputs/ populated (see README).
set -e
cd "$(dirname "$0")"; export PYTHONPATH=scripts
python3 -I scripts/dock3.py 1,2,3,4,5,6,7,8,9,10   # restraint docking -> ab{n}_docked.pdb
python3 -I scripts/prep2.py                          # align 3-fold axis -> target_prep.pdb, ab{n}_prep.pdb
mkdir -p frames out
python3 -I scripts/render.py 0 300 0 &               # PyMOL ray-traced frames (two processes)
python3 -I scripts/render.py 300 600 0 &
wait
python3 -I scripts/overlay.py 0 600                  # text, ipTM labels, progress bar
ffmpeg -y -framerate 20 -i out/f%04d.png -c:v libx264 -pix_fmt yuv420p -crf 20 -preset medium -movflags +faststart lassa_antibodies.mp4
