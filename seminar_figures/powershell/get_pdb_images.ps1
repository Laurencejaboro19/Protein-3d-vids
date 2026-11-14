<#
  get_pdb_images.ps1
  Downloads a structure image for every PDB entry used in the de novo protein
  design seminar, straight from the RCSB Protein Data Bank, and writes a
  CITATIONS.txt recording what each file is.

  Usage:  paste the whole thing into Windows PowerShell and press Enter.
          Nothing else to set up; it makes its own folder.

  Note on a bug this version fixes: an earlier draft did `$cite += ...` inside
  a function. PowerShell gives the function its OWN copy of that variable, so
  every line written inside the function was thrown away when the function
  returned and CITATIONS.txt came out nearly empty. The fix is to have the
  function RETURN its line and let the caller append it (see below).
#>

$ErrorActionPreference = 'Stop'
$outDir = Join-Path $env:USERPROFILE 'Downloads\pdbpics'
New-Item -ItemType Directory -Force -Path $outDir | Out-Null

# id, filename, what it is, experimental method, resolution
$entries = @(
  @{ id='4INS'; file='fig02a_4INS.png'; what='Insulin (Sus scrofa)';                      method='X-ray crystallography'; res='1.5 A'  },
  @{ id='1MBN'; file='fig02b_1MBN.png'; what='Myoglobin (sperm whale)';                   method='X-ray crystallography'; res='2.0 A'  },
  @{ id='1LYZ'; file='fig02c_1LYZ.png'; what='Hen egg-white lysozyme';                    method='X-ray crystallography'; res='2.0 A'  },
  @{ id='1A3N'; file='fig02d_1A3N.png'; what='Human deoxyhaemoglobin';                    method='X-ray crystallography'; res='1.8 A'  },
  @{ id='1MBN'; file='fig03a_1MBN.png'; what='Myoglobin, alpha-helix example';            method='X-ray crystallography'; res='2.0 A'  },
  @{ id='1EMA'; file='fig03b_1EMA.png'; what='Green fluorescent protein, beta barrel';    method='X-ray crystallography'; res='1.9 A'  },
  @{ id='7KI0'; file='fig05a_7KI0.png'; what='Semaglutide-GLP-1 receptor-Gs complex';     method='Cryo-electron microscopy'; res='2.50 A' },
  @{ id='1N8Z'; file='fig05b_1N8Z.png'; what='HER2 with Herceptin Fab';                   method='X-ray crystallography'; res='2.52 A' },
  @{ id='8SK7'; file='fig07_8SK7.png';  what='Designed binder with its target';           method='X-ray crystallography'; res='2.93 A' },
  @{ id='7JZU'; file='fig11_7JZU.png';  what='LCB1 with SARS-CoV-2 spike RBD';            method='X-ray crystallography'; res='3.1 A'  },
  @{ id='6DG5'; file='fig12_6DG5.png';  what='Neo-2/15 with its receptor';                method='X-ray crystallography'; res='-'      },
  @{ id='2B5I'; file='fig12opt_2B5I.png'; what='Natural interleukin-2 with receptor';     method='X-ray crystallography'; res='-'      },
  @{ id='9BK5'; file='fig13_9BK5.png';  what='Designed protein with three-finger toxin';  method='X-ray crystallography'; res='2.68 A' },
  @{ id='9NFU'; file='fig14_9NFU.png';  what='Designed scFv with C. difficile toxin B';   method='Cryo-electron microscopy'; res='3.60 A' },
  @{ id='8GJI'; file='fig15a_8GJI.png'; what='Designed binder of a helical peptide hormone'; method='X-ray crystallography'; res='-'   },
  @{ id='9DEG'; file='fig15b_9DEG.png'; what='Designed serine hydrolase';                 method='X-ray crystallography'; res='-'      },
  @{ id='7SGE'; file='fig10_7SGE.png';  what='SKYCovione designed nanoparticle antigen';  method='Cryo-electron microscopy'; res='-'   }
)

# Returns the citation line, or $null on failure. It does NOT touch $cite.
function Get-PdbImage {
  param($entry, $outDir)
  $id   = $entry.id.ToUpper()
  $dest = Join-Path $outDir $entry.file

  # RCSB serves a ready-made structure image per entry; try the large one first.
  $urls = @(
    "https://cdn.rcsb.org/images/structures/$($id.ToLower())_assembly-1.jpeg",
    "https://cdn.rcsb.org/images/structures/$id`_assembly-1.jpeg",
    "https://cdn.rcsb.org/images/structures/$($id.Substring(1,2).ToLower())/$($id.ToLower())/$($id.ToLower())_assembly-1.jpeg"
  )

  foreach ($u in $urls) {
    try {
      Invoke-WebRequest -Uri $u -OutFile $dest -UseBasicParsing -TimeoutSec 60
      if ((Get-Item $dest).Length -gt 5kb) {
        Write-Host ("  OK   {0,-22} {1}" -f $entry.file, $id) -ForegroundColor Green
        return ("{0}`t PDB {1}`t {2}`t {3}`t {4}`t {5}" -f `
                 $entry.file, $id, $entry.what, $entry.method, $entry.res, $u)
      }
    } catch { }
  }
  Write-Host ("  FAIL {0,-22} {1}" -f $entry.file, $id) -ForegroundColor Red
  return $null
}

$cite = New-Object System.Collections.Generic.List[string]
$cite.Add("file`t pdb`t contents`t method`t resolution`t source_url")

$ok = 0; $bad = 0
foreach ($e in $entries) {
  $line = Get-PdbImage -entry $e -outDir $outDir   # <- returned, not appended inside
  if ($line) { $cite.Add($line); $ok++ } else { $bad++ }
  Start-Sleep -Milliseconds 400                     # be polite to the CDN
}

$citePath = Join-Path $outDir 'CITATIONS.txt'
$cite | Set-Content -Path $citePath -Encoding UTF8

Write-Host ""
Write-Host "$ok downloaded, $bad failed" -ForegroundColor Cyan
Write-Host "Folder:    $outDir"
Write-Host "Citations: $citePath"
