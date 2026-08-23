$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

$RuntimeDir = Join-Path $PSScriptRoot "runtime"
$PythonExe = Join-Path $RuntimeDir "python.exe"
$Archive = Join-Path $RuntimeDir "python-embed.zip"
$Url = "https://www.python.org/ftp/python/3.13.5/python-3.13.5-embed-amd64.zip"

if (Test-Path $PythonExe) {
    Write-Host "Portable Python runtime is already installed." -ForegroundColor Green
    exit 0
}

New-Item -ItemType Directory -Force -Path $RuntimeDir | Out-Null
Write-Host "Downloading the portable Python runtime from python.org..." -ForegroundColor Cyan
Invoke-WebRequest -Uri $Url -OutFile $Archive -UseBasicParsing
Write-Host "Extracting runtime..." -ForegroundColor Cyan
Expand-Archive -Path $Archive -DestinationPath $RuntimeDir -Force
Remove-Item $Archive -Force

$Pth = Get-ChildItem $RuntimeDir -Filter "python*._pth" | Select-Object -First 1
if (-not $Pth) { throw "Python path configuration file was not found." }
$Lines = Get-Content $Pth.FullName
if ($Lines -notcontains "..") { $Lines += ".." }
Set-Content -Path $Pth.FullName -Value $Lines -Encoding ASCII

if (-not (Test-Path $PythonExe)) { throw "Portable Python setup did not produce python.exe." }
Write-Host "Portable runtime installed successfully." -ForegroundColor Green
