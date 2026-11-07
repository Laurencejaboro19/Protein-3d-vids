# Installs the Boltz command-line tool and signs you in through your browser. Worked on Windows PowerShell.
# Paste the three lines one block at a time. After "auth login" a browser tab opens; sign in to Boltz and approve.
irm https://install.boltz.bio/boltz-api/install.ps1 | iex
$bin = "$env:LOCALAPPDATA\Programs\Boltz\bin"
$env:Path += ";$bin"
[Environment]::SetEnvironmentVariable("Path", [Environment]::GetEnvironmentVariable("Path","User") + ";$bin", "User")
& "$bin\boltz-api.exe" auth login
# If it says "no such host", run:  Clear-DnsClientCache   and try the last line again.
# If no browser opens:  & "$bin\boltz-api.exe" auth login --device-code
