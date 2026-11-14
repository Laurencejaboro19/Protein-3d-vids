<#
  get_graphical_abstracts.ps1

  Downloads the non-PDB pictures used in the seminar slides and report:
  instrument photographs, public-domain diagrams and the snakebite /
  monoclonal-antibody figures. Everything is pulled from Wikimedia Commons
  through the MediaWiki API, so the script also reads back the real title,
  author and licence of each file and writes them into CITATIONS.txt. That
  way the credit line under every figure comes from the file itself rather
  than from memory.

  Usage: paste the whole script into Windows PowerShell and press Enter.
         It creates its own folder; nothing to set up first.

  Scope bug this version fixes
  ----------------------------
  The first draft did `$cite += $line` INSIDE the download function. PowerShell
  hands a function its own copy of a variable from the caller's scope, so every
  line appended in there vanished when the function returned: 12 images came
  down but CITATIONS.txt had only 2 entries. The fix is for the function to
  RETURN its line and for the caller to append it.
#>

$ErrorActionPreference = 'Stop'
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

$outDir = Join-Path $env:USERPROFILE 'Downloads\graphical abstract'
New-Item -ItemType Directory -Force -Path $outDir | Out-Null

$UA = 'seminar-figure-fetch/1.0 (university coursework; contact via GitHub Laurencejaboro19)'

# saveAs  =  what the file is called on disk
# commons =  the exact File: page on Wikimedia Commons
$items = @(
  @{ saveAs='fig01a_amino_acid_structure.png'; commons='File:Amino Acid.JPG' },
  @{ saveAs='fig01b_peptide_bond.png';         commons='File:Peptidformationball mk.svg' },
  @{ saveAs='fig04a_xray_diffractometer.png';  commons='File:U.S. Department of Energy - Science - 354 027 001 (9787699981).jpg' },
  @{ saveAs='fig04b_cryoEM_microscope.png';    commons='File:Titan Krios University of Leeds.jpg' },
  @{ saveAs='fig04c_NMR_spectrometer.png';     commons='File:Nuclear magnetic resonance devices in CAFIA laboratory.png' },
  @{ saveAs='fig06b_induced_fit.png';          commons='File:Induced fit model en.svg' },
  @{ saveAs='fig14a_antivenom_milking.png';    commons='File:Venin Genève 24102014.jpg' },
  @{ saveAs='fig15a_immunise_monoclonals.png'; commons='File:Monoclonals.png' }
)

# Asks Commons for the real download URL plus the credit metadata.
# Returns a hashtable, or $null if the file could not be resolved.
function Get-CommonsInfo {
  param([string]$title)
  $api = 'https://commons.wikimedia.org/w/api.php'
  $q = @{
    action = 'query'; format = 'json'; prop = 'imageinfo'
    iiprop = 'url|extmetadata'; iiurlwidth = '1600'; titles = $title
  }
  $qs = ($q.GetEnumerator() | ForEach-Object {
            '{0}={1}' -f $_.Key, [uri]::EscapeDataString($_.Value) }) -join '&'
  try {
    $r = Invoke-RestMethod -Uri "$api`?$qs" -Headers @{ 'User-Agent' = $UA } -TimeoutSec 60
  } catch { return $null }

  $page = $r.query.pages.PSObject.Properties.Value | Select-Object -First 1
  if (-not $page.imageinfo) { return $null }
  $ii = $page.imageinfo[0]
  $m  = $ii.extmetadata

  # thumburl renders SVG to PNG at 1600px; plain url is the original file
  $dl = if ($ii.thumburl) { $ii.thumburl } else { $ii.url }

  # strip the HTML Commons puts in the artist field
  $artist = if ($m.Artist) { ($m.Artist.value -replace '<[^>]+>', '').Trim() } else { 'Unknown' }
  $lic    = if ($m.LicenseShortName) { $m.LicenseShortName.value } else { 'see source page' }

  return @{
    url     = $dl
    title   = $page.title
    author  = $artist
    licence = $lic
    source  = 'https://commons.wikimedia.org/wiki/' + ($page.title -replace ' ', '_')
  }
}

# Returns the citation block for one item (never appends to $cite itself).
function Get-Picture {
  param($item, [string]$outDir)
  $info = Get-CommonsInfo -title $item.commons
  if (-not $info) {
    Write-Host ("  FAIL {0}  (could not resolve on Commons)" -f $item.saveAs) -ForegroundColor Red
    return "{0}`n  NOT DOWNLOADED - resolve by hand: {1}`n" -f $item.saveAs, $item.commons
  }

  $dest = Join-Path $outDir $item.saveAs
  try {
    Invoke-WebRequest -Uri $info.url -OutFile $dest -UseBasicParsing `
                      -Headers @{ 'User-Agent' = $UA } -TimeoutSec 120
  } catch {
    Write-Host ("  FAIL {0}  ({1})" -f $item.saveAs, $_.Exception.Message) -ForegroundColor Red
    return "{0}`n  NOT DOWNLOADED - url: {1}`n" -f $item.saveAs, $info.url
  }

  if ((Get-Item $dest).Length -lt 3kb) {
    Remove-Item $dest -Force -ErrorAction SilentlyContinue
    Write-Host ("  FAIL {0}  (file too small)" -f $item.saveAs) -ForegroundColor Red
    return "{0}`n  NOT DOWNLOADED - url: {1}`n" -f $item.saveAs, $info.url
  }

  Write-Host ("  OK   {0}" -f $item.saveAs) -ForegroundColor Green
  return @"
$($item.saveAs)
  Title   : $($info.title)
  Author  : $($info.author)
  Licence : $($info.licence)
  Source  : $($info.source)

"@
}

$cite = New-Object System.Collections.Generic.List[string]
$cite.Add('SEMINAR FIGURE SOURCES')
$cite.Add('Generated ' + (Get-Date -Format 'yyyy-MM-dd HH:mm'))
$cite.Add(('=' * 60))
$cite.Add('')

foreach ($i in $items) {
  $cite.Add((Get-Picture -item $i -outDir $outDir))   # <- returned, then appended here
  Start-Sleep -Milliseconds 500                        # be polite to the API
}

$citePath = Join-Path $outDir 'CITATIONS.txt'
$cite | Set-Content -Path $citePath -Encoding UTF8

Write-Host ''
Write-Host "Folder:    $outDir"
Write-Host "Citations: $citePath"
