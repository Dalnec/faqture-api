import gzip
import os
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from base.backup.send_drive import searchFile
from logger import log
from config import CONFIG

# File paths
BACKUP_FILE = Path(f"{CONFIG.db_bk_name}.backup")
COMPRESSED_FILE = Path(f"{BACKUP_FILE}.gz")
DRIVE_ENABLED = CONFIG.db_drive

def backup():
    """Create database backup if not already done today."""
    if _is_backup_current():
        log.info('Backup already done today')
        return
    
    _create_backup()

def _is_backup_current() -> bool:
    """Check if backup file exists and was created today."""
    if not COMPRESSED_FILE.exists():
        return False

    file_date = datetime.fromtimestamp(COMPRESSED_FILE.stat().st_mtime).date()
    return file_date == datetime.now().date()


def _create_backup():
    """Create and compress database backup."""
    log.info('Creating database backup...')
    
    try:
        # Create database dump
        _run_pg_dump()
        
        # Compress the backup
        _compress_backup()
        
        # Upload to drive if enabled
        if DRIVE_ENABLED:
            _upload_to_drive()
            
        log.info(f'Backup completed: {COMPRESSED_FILE}')
        
    except subprocess.CalledProcessError as e:
        log.error(f'Backup failed: {e}')
        raise
    except Exception as e:
        log.error(f'Unexpected error during backup: {e}')
        raise


def _run_pg_dump():
    """Execute pg_dump command."""
    env = os.environ.copy()
    env["PGPASSWORD"] = CONFIG.db_pass
    
    cmd = [
        "pg_dump",
        "-d", CONFIG.db_name,
        "-p", str(CONFIG.db_port),
        "-U", CONFIG.db_user,
        "-F", "t",
        "-f", str(BACKUP_FILE)
    ]
    
    subprocess.run(cmd, env=env, check=True)


def _compress_backup():
    """Compress the backup file using gzip."""
    with open(BACKUP_FILE, 'rb') as f_in:
        with gzip.open(COMPRESSED_FILE, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)
    
    # Remove uncompressed file to save space
    BACKUP_FILE.unlink()


def _upload_to_drive():
    """Upload compressed backup to drive."""
    searchFile(100, f"name='{COMPRESSED_FILE.name}'", str(COMPRESSED_FILE))