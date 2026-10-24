# Copies the 20 .cif files into one small zip named rank01.cif ... rank20.cif (the names build_boltz_complexes.py expects).
$src = "$env:USERPROFILE\Downloads\GLP1R_boltz"
$dst = "$env:USERPROFILE\Downloads\GLP1R_cifs_only"
Remove-Item $dst -Recurse -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force -Path $dst | Out-Null
Get-ChildItem $src -Recurse -Filter *.cif | ForEach-Object {
  $rank = ($_.FullName -split '\\GLP1R_boltz\\')[1].Split('\')[0].Substring(0,2)
  Copy-Item $_.FullName "$dst\rank$rank.cif"
}
Compress-Archive -Path "$dst\*" -DestinationPath "$env:USERPROFILE\Downloads\GLP1R_cifs_only.zip" -Force
