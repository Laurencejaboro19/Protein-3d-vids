# Builds the video from Downloads\KRAS_video_cifs.zip. Needs Python 3 and ffmpeg on PATH, and this repo cloned (branch kras).
# One-time installs (run once):  pip install gemmi numpy playwright pillow ; python -m playwright install chromium
# Usage:  .\04_make_video.ps1 -Repo "C:\path\to\Protein-3d-vids"
# Rendering takes about 10-15 minutes (software WebGL). Output: Downloads\KRAS_video\kras_binders.mp4
param([string]$Repo = "$env:USERPROFILE\Downloads\Protein-3d-vids")
$dl   = "$env:USERPROFILE\Downloads"
$work = "$dl\KRAS_video\render"
$src  = "$Repo\kras_binder_video"
Remove-Item $work -Recurse -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force -Path "$work\bz" | Out-Null
Expand-Archive "$dl\KRAS_video_cifs.zip" -DestinationPath "$work\unz" -Force
Move-Item "$work\unz\*.cif" "$work\bz"
Move-Item "$work\unz\top20.csv" "$work\top20.csv"
Copy-Item "$src\page_kras.html","$src\render_kras.py","$src\3Dmol-min.js" $work
python "$src\build_kras.py" $work
Push-Location $work
python render_kras.py 8118
ffmpeg -y -framerate 24 -i fr_kras/f%04d.png -c:v libx264 -pix_fmt yuv420p -crf 18 -movflags +faststart "$dl\KRAS_video\kras_binders.mp4"
Pop-Location
Write-Host "Done: $dl\KRAS_video\kras_binders.mp4" -ForegroundColor Green
