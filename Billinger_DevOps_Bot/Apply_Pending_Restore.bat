@echo off
setlocal
cd /d "%~dp0"
echo [*] Restoring latest backup from backups/ directory...
python -c "from storage.backup_manager import backup_manager; print('Backups available:', len(backup_manager.list_backups()))"
pause
