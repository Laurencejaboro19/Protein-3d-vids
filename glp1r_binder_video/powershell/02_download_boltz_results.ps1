# Downloads 20 finished Boltz structure-and-binding jobs and zips them. This is the script that worked (20 of 20 .cif found).
# Put your own prediction ids in $ids, in rank order (rank 1 first). Results stay on Boltz for 7 days after a job finishes.
$bz  = "$env:LOCALAPPDATA\Programs\Boltz\bin\boltz-api.exe"
$out = "$env:USERPROFILE\Downloads\GLP1R_boltz"
New-Item -ItemType Directory -Force -Path $out | Out-Null
$ids = @(
"sab_pred_REPLACE_rank01","sab_pred_REPLACE_rank02"   # ... 20 ids, rank order
)
for ($i = 0; $i -lt $ids.Count; $i++) {
  $name = "{0:D2}_{1}" -f ($i + 1), $ids[$i]
  Write-Host "Downloading $name" -ForegroundColor Cyan
  & $bz download-results --id $ids[$i] --run-dir "$out\$name"
}
Write-Host "File types downloaded:"
Get-ChildItem $out -Recurse -File | Group-Object Extension | Format-Table Name, Count
$cifs = (Get-ChildItem $out -Recurse -Filter *.cif).Count
Write-Host "CIF structures found: $cifs of 20" -ForegroundColor Yellow
Compress-Archive -Path "$out\*" -DestinationPath "$env:USERPROFILE\Downloads\GLP1R_boltz_cifs.zip" -Force
