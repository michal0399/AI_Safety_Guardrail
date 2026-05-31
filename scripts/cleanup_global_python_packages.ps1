<#
Safe script to detect and optionally uninstall globally-installed Python packages.
Caveats:
#>

# script parameters
param(
    [switch]$IncludeUser
)

if ($IncludeUser) { Write-Host "Including packages installed under user profile in candidates." -ForegroundColor Yellow }

# Require Python on PATH
try {
    $py = & python -V 2>$null
} catch {
    Write-Error "Python not found on PATH. Activate system python or adjust PATH."
    exit 2
}

# Detect virtualenv
$inVenv = & python -c "import sys; print(sys.prefix != getattr(sys, 'base_prefix', sys.prefix))"

if ($inVenv.Trim() -eq 'True') {
    Write-Host "It looks like you're inside a virtual environment. Deactivate it before running this script." -ForegroundColor Yellow
    exit 1
}

Write-Host "Scanning installed pip packages..."
$pkgJson = & python -m pip list --format=json 2>$null
if (!$pkgJson) {
    Write-Error "Failed to enumerate pip packages."
    exit 3
}

$pkgs = $pkgJson | ConvertFrom-Json
$rows = @()
foreach ($p in $pkgs) {
    if ($p.name -in @('pip','setuptools','wheel')) { continue }
    $show = & python -m pip show $($p.name) 2>$null | Out-String
    $locLine = ($show -split "\r?\n" | Where-Object { $_ -like 'Location:*' }) -join ''
    $location = $locLine -replace 'Location:\s*',''
    $rows += [PSCustomObject]@{Name=$p.name; Version=$p.version; Location=$location}
}

if ($rows.Count -eq 0) {
    Write-Host "No installed packages found."
    exit 0
}

Write-Host "\nAll installed packages (sample):"
$rows | Sort-Object Location,Name | Select-Object -First 20 | Format-Table -AutoSize

# Heuristic: packages outside the user's profile directory are likely system/global installs
$userPrefix = $env:USERPROFILE.TrimEnd('\')
if ($IncludeUser) {
    $globalCandidates = $rows
} else {
    $globalCandidates = $rows | Where-Object { $_.Location -and ($_.Location -notlike "$userPrefix*") }
}

if ($globalCandidates.Count -eq 0) {
    Write-Host "\nNo packages matched the selection criteria."
    exit 0
}

Write-Host "\nDetected packages that match selection (potential candidates):" -ForegroundColor Cyan
$globalCandidates | Format-Table -AutoSize

$confirm = Read-Host "Type 'yes' to uninstall ALL listed packages (irreversible)"
if ($confirm -ne 'yes') {
    Write-Host 'Aborting. No changes made.'
    exit 0
}

foreach ($r in $globalCandidates) {
    Write-Host "Uninstalling $($r.Name) ..."
    & python -m pip uninstall -y $($r.Name)
}

Write-Host "Finished. Consider using virtual environments (`python -m venv .venv`) or `pipx` for global CLI tools." -ForegroundColor Green
