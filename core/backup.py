"""Database backup helper (SQLite file copy or dump)."""
import os
import shutil
from datetime import datetime
from pathlib import Path

from django.conf import settings


def create_backup(user=None, notes=''):
    from core.platform_models import PlatformBackup

    backup_dir = Path(settings.BASE_DIR) / 'backups'
    backup_dir.mkdir(exist_ok=True)
    stamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    filename = f'backup_{stamp}.sqlite3'
    dest = backup_dir / filename

    db = settings.DATABASES['default']
    engine = db.get('ENGINE', '')
    size = 0

    if 'sqlite' in engine:
        src = Path(db['NAME'])
        if src.exists():
            shutil.copy2(src, dest)
            size = dest.stat().st_size
        else:
            dest.write_text('')
    else:
        # For Postgres: write a marker + instructions; full pg_dump needs shell
        filename = f'backup_{stamp}.sql.txt'
        dest = backup_dir / filename
        dest.write_text(
            f'# Run: pg_dump {db.get("NAME")} > {filename}\n'
            f'# Created at {stamp} UTC\n'
        )
        size = dest.stat().st_size

    return PlatformBackup.objects.create(
        filename=filename,
        path=str(dest),
        size_bytes=size,
        created_by=user,
        notes=notes or 'Manual backup',
    )
