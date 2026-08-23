$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
Write-Host "Billinger DevOps Bot v2.6.2 - Adaptive AI Mentor Edition" -ForegroundColor Cyan
$Portable = Join-Path $PSScriptRoot "runtime\python.exe"
if (Test-Path $Portable) {
    & $Portable (Join-Path $PSScriptRoot "app.py")
} elseif (Get-Command py -ErrorAction SilentlyContinue) {
    & py -3 (Join-Path $PSScriptRoot "app.py")
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    & python (Join-Path $PSScriptRoot "app.py")
} else {
    & (Join-Path $PSScriptRoot "Setup_Portable_Runtime.ps1")
    & $Portable (Join-Path $PSScriptRoot "app.py")
}
