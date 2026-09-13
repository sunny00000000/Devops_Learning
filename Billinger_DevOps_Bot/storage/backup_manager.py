import os
import shutil
import zipfile
import hashlib
import time
from pathlib import Path
from core.configuration.config import Config, BACKUP_DIR
from core.logging.logger import logger
from core.errors.exceptions import ValidationError, BillingerError

class BackupManager:
    @staticmethod
    def create_backup(label: str = "manual") -> dict:
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        backup_filename = f"billinger_backup_{label}_{timestamp}.zip"
        backup_path = BACKUP_DIR / backup_filename
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        
        try:
            with zipfile.ZipFile(backup_path, "w", zipfile.ZIP_DEFLATED) as zipf:
                if os.path.exists(Config.DB_PATH):
                    zipf.write(Config.DB_PATH, arcname="data/billinger.db")
                if os.path.exists(Config.TOKEN_DIR):
                    for root, _, files in os.walk(Config.TOKEN_DIR):
                        for f in files:
                            full = os.path.join(root, f)
                            rel = os.path.relpath(full, Config.BASE_DIR)
                            zipf.write(full, arcname=rel)

            hasher = hashlib.sha256()
            with open(backup_path, "rb") as f:
                while chunk := f.read(65536):
                    hasher.update(chunk)
            sha256_hash = hasher.hexdigest()

            checksum_file = BACKUP_DIR / f"{backup_filename}.sha256"
            with open(checksum_file, "w") as f:
                f.write(sha256_hash)

            logger.info(f"Backup created: {backup_filename} (SHA256: {sha256_hash[:12]}...)")
            return {
                "filename": backup_filename,
                "path": str(backup_path),
                "size_bytes": os.path.getsize(backup_path),
                "sha256": sha256_hash,
                "timestamp": timestamp
            }
        except Exception as e:
            logger.error(f"Backup creation failed: {e}")
            raise BillingerError(f"Failed to create backup: {e}")

    @staticmethod
    def restore_backup(backup_path_str: str) -> dict:
        backup_path = Path(backup_path_str)
        if not backup_path.exists():
            raise ValidationError(f"Backup file does not exist: {backup_path_str}")

        chk_path = Path(f"{backup_path_str}.sha256")
        if chk_path.exists():
            expected_hash = chk_path.read_text().strip()
            hasher = hashlib.sha256()
            with open(backup_path, "rb") as f:
                while chunk := f.read(65536):
                    hasher.update(chunk)
            if hasher.hexdigest() != expected_hash:
                raise ValidationError("Backup checksum mismatch! Tampering or corruption detected.")

        pre_rollback = BACKUP_DIR / f"pre_restore_snapshot_{int(time.time())}.db"
        if os.path.exists(Config.DB_PATH):
            shutil.copy2(Config.DB_PATH, pre_rollback)

        try:
            with zipfile.ZipFile(backup_path, "r") as zipf:
                for member in zipf.namelist():
                    norm = os.path.normpath(member)
                    if norm.startswith("..") or os.path.isabs(norm):
                        raise ValidationError(f"Security hazard in backup zip path: {member}")
                if "data/billinger.db" in zipf.namelist():
                    zipf.extract("data/billinger.db", path=Config.BASE_DIR)
            logger.info(f"Restored backup from {backup_path_str} successfully.")
            return {"status": "SUCCESS", "restored_from": str(backup_path)}
        except Exception as e:
            if pre_rollback.exists():
                shutil.copy2(pre_rollback, Config.DB_PATH)
            logger.error(f"Restore failed, rolled back: {e}")
            raise BillingerError(f"Restore failed: {e}")

backup_manager = BackupManager()
