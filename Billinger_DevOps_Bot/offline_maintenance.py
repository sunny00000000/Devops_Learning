#!/usr/bin/env python3
"""Offline update/restore helper. Run only while the Billinger server is closed."""
from __future__ import annotations
import argparse, datetime as dt, json, shutil, sys, tempfile, zipfile
from pathlib import Path, PurePosixPath

BASE = Path(__file__).resolve().parent
PRESERVE = {"data", "student_workspaces", "certificates", "backups", "resumes", "labs", "runtime", "imports", "updates", "portfolios", "career_data", "mail_outbox"}

def safe_extract(zf: zipfile.ZipFile, dest: Path) -> None:
    infos = zf.infolist()
    if not infos or len(infos) > 10000:
        raise RuntimeError("Archive is empty or contains too many entries.")
    total = 0
    root = dest.resolve()
    for info in infos:
        p = PurePosixPath(info.filename.replace("\\", "/"))
        if p.is_absolute() or ".." in p.parts or "\x00" in info.filename:
            raise RuntimeError(f"Unsafe archive path: {info.filename}")
        mode = (info.external_attr >> 16) & 0o170000
        if mode == 0o120000:
            raise RuntimeError(f"Symbolic links are not permitted: {info.filename}")
        if info.flag_bits & 0x1:
            raise RuntimeError(f"Encrypted archive entries are not permitted: {info.filename}")
        if not info.is_dir():
            if info.file_size > 4 * 1024 * 1024 * 1024:
                raise RuntimeError(f"Archive member is too large: {info.filename}")
            total += info.file_size
            if total > 5 * 1024 * 1024 * 1024:
                raise RuntimeError("Expanded archive exceeds the 5 GB safety limit.")
            if info.file_size > 1024 * 1024 and info.file_size / max(1, info.compress_size) > 200:
                raise RuntimeError(f"Unsafe compression ratio: {info.filename}")
        target = (dest / Path(*p.parts)).resolve()
        if root != target and root not in target.parents:
            raise RuntimeError(f"Unsafe archive path: {info.filename}")
    bad = zf.testzip()
    if bad:
        raise RuntimeError(f"Archive integrity check failed at: {bad}")
    zf.extractall(dest)


def runtime_python() -> str:
    return sys.executable

def preflight_closed() -> None:
    # SQLite sidecars are a useful indicator; the user should still close the command window.
    if (BASE / "data" / "billinger.db-wal").exists():
        raise RuntimeError("The bot appears to be running. Close the Billinger command window first.")

def locate_update_root(root: Path) -> Path:
    candidates = [p.parent for p in root.rglob("VERSION.txt") if p.is_file()]
    candidates = [p for p in candidates if (p / "app.py").is_file() and (p / "static").is_dir()]
    if not candidates:
        raise RuntimeError("Could not find an application root containing VERSION.txt and app.py.")
    return min(candidates, key=lambda p: len(p.parts))

def apply_update() -> None:
    preflight_closed()
    pending_path = BASE / "updates" / "pending_update.json"
    if not pending_path.is_file():
        raise RuntimeError("No staged update was found.")
    pending = json.loads(pending_path.read_text(encoding="utf-8"))
    archive = Path(pending["path"])
    if not archive.is_file():
        raise RuntimeError("The staged update ZIP is missing.")
    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    safety = BASE / "backups" / f"pre_update_files_{stamp}.zip"
    safety.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(safety, "w", zipfile.ZIP_DEFLATED) as zf:
        for name in ("app.py", "v2_features.py", "v23_features.py", "v24_features.py", "offline_maintenance.py", "VERSION.txt", "README.md"):
            path = BASE / name
            if path.is_file(): zf.write(path, name)
        for folder in ("static", "content", "tests", "docs"):
            path = BASE / folder
            if path.is_dir():
                for file in path.rglob("*"):
                    if file.is_file(): zf.write(file, file.relative_to(BASE).as_posix())
    with tempfile.TemporaryDirectory() as td:
        extracted = Path(td)
        with zipfile.ZipFile(archive) as zf: safe_extract(zf, extracted)
        source = locate_update_root(extracted)
        for item in source.iterdir():
            if item.name in PRESERVE or item.name.startswith("."):
                continue
            target = BASE / item.name
            if item.is_dir():
                if target.exists(): shutil.rmtree(target)
                shutil.copytree(item, target)
            else:
                shutil.copy2(item, target)
    pending_path.unlink(missing_ok=True)
    print(f"Update applied successfully. Safety copy: {safety.name}")

def apply_restore() -> None:
    preflight_closed()
    pending_path = BASE / "updates" / "pending_restore" / "pending.json"
    if not pending_path.is_file():
        raise RuntimeError("No staged restore was found.")
    pending = json.loads(pending_path.read_text(encoding="utf-8"))
    archive = Path(pending["path"])
    if not archive.is_file(): raise RuntimeError("The staged backup ZIP is missing.")
    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    current_db = BASE / "data" / "billinger.db"
    if current_db.is_file():
        safety = BASE / "backups" / f"pre_restore_database_{stamp}.db"
        safety.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(current_db, safety)
    with tempfile.TemporaryDirectory() as td:
        extracted = Path(td)
        with zipfile.ZipFile(archive) as zf: safe_extract(zf, extracted)
        db = extracted / "data" / "billinger.db"
        if not db.is_file(): raise RuntimeError("Backup does not contain data/billinger.db.")
        (BASE / "data").mkdir(parents=True, exist_ok=True); shutil.copy2(db, current_db)
        for folder in ("student_workspaces", "certificates", "resumes", "labs"):
            src = extracted / folder
            if src.is_dir():
                dst = BASE / folder
                if dst.exists(): shutil.rmtree(dst)
                shutil.copytree(src, dst)
    pending_path.unlink(missing_ok=True)
    print("Backup restored successfully.")

def main() -> None:
    parser=argparse.ArgumentParser(); parser.add_argument("mode", choices=["update","restore"]); args=parser.parse_args()
    try:
        apply_update() if args.mode=="update" else apply_restore()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr); raise SystemExit(1)

if __name__ == "__main__": main()
