#!/usr/bin/env python3
"""
Database backup script for wzrysjglz.
Creates timestamped backups of the SQLite database.
Keeps the last 30 backups by default.
"""
import os
import shutil
import glob
from datetime import datetime
from pathlib import Path


def backup_database():
    """Create a backup of the database."""
    # Configuration
    db_path = Path(__file__).parent.parent / "data" / "data.db"
    backup_dir = Path(__file__).parent.parent / "backups"
    max_backups = 30

    # Check if database exists
    if not db_path.exists():
        print(f"Database not found: {db_path}")
        return False

    # Create backup directory
    backup_dir.mkdir(exist_ok=True)

    # Create backup filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"data_{timestamp}.db"
    backup_path = backup_dir / backup_filename

    try:
        # Copy database file
        shutil.copy2(db_path, backup_path)
        print(f"Backup created: {backup_path}")

        # Clean up old backups
        cleanup_old_backups(backup_dir, max_backups)

        return True
    except Exception as e:
        print(f"Backup failed: {e}")
        return False


def cleanup_old_backups(backup_dir: Path, max_backups: int):
    """Remove old backups, keeping only the most recent ones."""
    backup_files = sorted(
        glob.glob(str(backup_dir / "data_*.db")),
        key=os.path.getmtime,
        reverse=True,
    )

    # Remove excess backups
    for old_backup in backup_files[max_backups:]:
        try:
            os.remove(old_backup)
            print(f"Removed old backup: {old_backup}")
        except Exception as e:
            print(f"Failed to remove {old_backup}: {e}")


if __name__ == "__main__":
    print("Starting database backup...")
    success = backup_database()
    if success:
        print("Backup completed successfully!")
    else:
        print("Backup failed!")
        exit(1)
