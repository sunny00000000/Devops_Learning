@echo off
setlocal
cd /d "%~dp0"
echo [*] Running Billinger 3-Tier Security Sandbox Defensive Tests...
python -c "import security.guard as g; r = g.command_guard.classify('rm -rf /'); assert r.tier.name == 'BLOCKED'; print('PASS: Command Guard blocked destructive host command.')"
pause
