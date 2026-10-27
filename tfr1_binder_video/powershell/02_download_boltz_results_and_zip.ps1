# Downloads the 20 finished Boltz-2.1 structure-and-binding jobs and zips the .cif files as rank01.cif ... rank20.cif.
# This is the block that worked (CIF structures found: 20 of 20). Put your own 20 prediction ids in $ids, in rank order.
# Results stay on Boltz for 7 days after a job finishes. If fewer than 20 .cif are found, wait a few minutes and run it again.
$bz  = "$env:LOCALAPPDATA\Programs\Boltz\bin\boltz-api.exe"
$out = "$env:USERPROFILE\Downloads\TfR1_boltz"
New-Item -ItemType Directory -Force -Path $out | Out-Null
$ids = @(
"sab_pred_REPLACE_rank01","sab_pred_REPLACE_rank02"   # ... 20 ids, rank order
)
for ($i = 0; $i -lt $ids.Count; $i++) {
  $name = "{0:D2}_{1}" -f ($i + 1), $ids[$i]
  Write-Host "Downloading $name" -ForegroundColor Cyan
  & $bz download-results --id $ids[$i] --run-dir "$out\$name"
}
$cifs = (Get-ChildItem $out -Recurse -Filter *.cif).Count
Write-Host "CIF structures found: $cifs of 20" -ForegroundColor Yellow
$dst = "$env:USERPROFILE\Downloads\TfR1_cifs_only"
Remove-Item $dst -Recurse -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force -Path $dst | Out-Null
Get-ChildItem $out -Recurse -Filter *.cif | ForEach-Object {
  $rank = ($_.FullName -split '\\TfR1_boltz\\')[1].Split('\')[0].Substring(0,2)
  Copy-Item $_.FullName "$dst\rank$rank.cif"
}
Compress-Archive -Path "$dst\*" -DestinationPath "$env:USERPROFILE\Downloads\TfR1_cifs_only.zip" -Force
Write-Host "Zip: $env:USERPROFILE\Downloads\TfR1_cifs_only.zip  ($((Get-ChildItem $dst).Count) files)" -ForegroundColor Green
