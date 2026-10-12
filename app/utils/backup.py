import os
import shutil
import sqlite3
import datetime
from pathlib import Path

BACKUP_DIR = Path("data/backups")
DB_PATH = Path("data/erp.db")

def ensure_backup_dir():
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)

def create_backup(label: str = "auto") -> str:
    """
    Creates a timestamped snapshot copy of the SQLite database.
    Returns the backup filename.
    """
    ensure_backup_dir()
    if not DB_PATH.exists():
        return ""
        
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"erp_backup_{label}_{timestamp}.db"
    backup_path = BACKUP_DIR / backup_filename
    
    # Use SQLite's online backup API for safe live backup
    src_conn = sqlite3.connect(DB_PATH)
    dst_conn = sqlite3.connect(backup_path)
    with dst_conn:
        src_conn.backup(dst_conn)
    dst_conn.close()
    src_conn.close()
    
    # Prune old backups if more than 30 exist
    _cleanup_old_backups(max_keep=30)
    
    return str(backup_path)

def list_backups() -> list:
    """
    Lists all available backup files with size and creation time.
    """
    ensure_backup_dir()
    backups = []
    for file in sorted(BACKUP_DIR.glob("*.db"), key=os.path.getmtime, reverse=True):
        stat = file.stat()
        backups.append({
            "filename": file.name,
            "filepath": str(file),
            "size_kb": round(stat.st_size / 1024, 2),
            "created_at": datetime.datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
        })
    return backups

def restore_backup(filename: str) -> bool:
    """
    Restores the database from a backup file.
    Creates a safety backup of current database first.
    """
    backup_path = BACKUP_DIR / filename
    if not backup_path.exists():
        return False
        
    # Safety backup before overwriting
    if DB_PATH.exists():
        create_backup(label="pre_restore_safety")
        
    # Restore
    src_conn = sqlite3.connect(backup_path)
    dst_conn = sqlite3.connect(DB_PATH)
    with dst_conn:
        src_conn.backup(dst_conn)
    dst_conn.close()
    src_conn.close()
    return True

def _cleanup_old_backups(max_keep: int = 30):
    try:
        backups = sorted(BACKUP_DIR.glob("*.db"), key=os.path.getmtime)
        if len(backups) > max_keep:
            for old_file in backups[:-max_keep]:
                old_file.unlink()
    except Exception as e:
        print(f"Error cleaning backups: {e}")
