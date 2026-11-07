# Downloads the 20 finished refolds, keeps one .cif per job as rankNN.cif and zips them with the CSV.
# This is the block that worked (CIF structures found: 20 of 20). Results stay on Boltz for 7 days after a job finishes.
# Reads the ids from Downloads\KRAS_video\job_ids.txt (written by 02), or paste your 20 ids into $ids yourself.
$bz   = "$env:LOCALAPPDATA\Programs\Boltz\bin\boltz-api.exe"
$dl   = "$env:USERPROFILE\Downloads"
$work = "$dl\KRAS_video"
$res  = "$work\boltz"
$stage= "$work\stage"
New-Item -ItemType Directory -Force -Path $res | Out-Null
$ids = @(Get-Content "$work\job_ids.txt" | Where-Object { $_.Trim() })
for ($i = 0; $i -lt $ids.Count; $i++) {
  $name = "{0:D2}_{1}" -f ($i + 1), $ids[$i]
  Write-Host "Downloading $name" -ForegroundColor Cyan
  & $bz download-results --id $ids[$i] --run-dir "$res\$name"
}
Remove-Item $stage -Recurse -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force -Path $stage | Out-Null
$n = 0
for ($i = 0; $i -lt $ids.Count; $i++) {
  $name = "{0:D2}_{1}" -f ($i + 1), $ids[$i]
  $cif = Get-ChildItem "$res\$name" -Recurse -Filter *.cif -ErrorAction SilentlyContinue | Select-Object -First 1
  if ($cif) { Copy-Item $cif.FullName ("$stage\rank{0:D2}.cif" -f ($i + 1)); $n++ }
}
Write-Host "CIF structures found: $n of 20" -ForegroundColor Yellow
$csv = "$dl\kras_FINAL20_with_sequences.csv"
if (Test-Path $csv) { Copy-Item $csv "$stage\top20.csv" } else { Write-Host "CSV not found: $csv" -ForegroundColor Red }
$zip = "$dl\KRAS_video_cifs.zip"
Compress-Archive -Path "$stage\*" -DestinationPath $zip -Force
Write-Host "Zip ready: $zip ($((Get-ChildItem $stage).Count) files)" -ForegroundColor Green
