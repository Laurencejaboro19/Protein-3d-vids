# Starts the 20 Boltz-2.1 structure-and-binding refolds (G12D complex + one binder each) with the Boltz command-line tool.
# NOTE: for the video, the 20 jobs were started through the Boltz connector in Claude with exactly this input (same entities, msa empty for peptide and binder).
# This CLI version builds the identical request but was not run end-to-end here. If a call is rejected, the error text says which field to change.
# Needs: Downloads\kras_FINAL20_with_sequences.csv (columns rank, sequence). Writes Downloads\KRAS_video\job_ids.txt (one id per rank, in rank order).
$bz   = "$env:LOCALAPPDATA\Programs\Boltz\bin\boltz-api.exe"
$dl   = "$env:USERPROFILE\Downloads"
$work = "$dl\KRAS_video"
New-Item -ItemType Directory -Force -Path $work | Out-Null
$hla = "GSHSMRYFYTSVSRPGRGEPRFIAVGYVDDTQFVRFDSDAASQRMEPRAPWIEQEGPEYWDQETRNVKAQSQTDRVDLGTLRGYYNQSEDGSHTIQIMYGCDVGPDGRFLRGYRQDAYDGKDYIALNEDLRSWTAADMAAQITKRKWEAAHAAEQQRAYLEGRCVEWLRRYLENGKETLQRTDPPKTHMTHHPISDHEATLRCWALGFYPAEITLTWQRDGEDQTQDTELVETRPAGDGTFQKWAAVVVPSGEEQRYTCHVQHEGLPKPLTLRWEP"
$b2m = "IQRTPKIQVYSRHPAENGKSNFLNCYVSGFHPSDIEVDLLKNGERIEKVEHSDLSFSKDWSFYLLYYTEFTPTEKDEYACRVNHVTLSQPKIVKWDRDM"
$pep = "VVVGADGVGK"
$rows = Import-Csv "$dl\kras_FINAL20_with_sequences.csv" | Sort-Object { [int]$_.rank }
$ids = @()
foreach ($r in $rows) {
  $body = @{
    entities = @(
      @{ type="protein"; chain_ids=@("A"); value=$hla },
      @{ type="protein"; chain_ids=@("B"); value=$b2m },
      @{ type="protein"; chain_ids=@("C"); value=$pep; msa=@{ type="empty" } },
      @{ type="protein"; chain_ids=@("D"); value=$r.sequence; msa=@{ type="empty" } }
    )
    binding = @{ type="protein_protein_binding"; binder_chain_ids=@("D") }
    num_samples = 1
  } | ConvertTo-Json -Depth 6
  Write-Host ("Starting rank {0} ({1}, {2} aa)" -f $r.rank, $r.id, $r.sequence.Length) -ForegroundColor Cyan
  $out = $body | & $bz --format raw predictions:structure-and-binding start
  $id = ($out | ConvertFrom-Json).id
  Write-Host "  job id: $id"
  $ids += $id
}
$ids | Set-Content "$work\job_ids.txt"
Write-Host "Saved $($ids.Count) job ids to $work\job_ids.txt. Wait a few minutes, then run 03_download_results_and_zip.ps1" -ForegroundColor Green
