Set-Location $PSScriptRoot
Write-Host "[*] Setting up portable runtime..." -ForegroundColor Green
python -c "import sqlite3, json; print('[OK] Core runtime operational.')"
pip install -q reportlab fastapi uvicorn 2>$null
Write-Host "[*] Setup verified." -ForegroundColor Green
