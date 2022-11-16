from pathlib import Path

from ..controller.backup import Backup
from ..controller.preset import Preset

__all__ = ['BackupManager']

class BackupManager:
    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super().__new__(cls)
        return cls.instance

    def get_backup_from_file(self, file_path: Path) -> Backup:
        raise NotImplementedError

    def create_backup(self, preset: Preset, force=False, keep=False) -> Backup:
        raise NotImplementedError

    def restore_backup(self, preset: Preset, backup: Backup) -> None:
        raise NotImplementedError

    def delete_backup(self, backup: Backup) -> None:
        raise NotImplementedError

    def rename_backup(self, backup: Backup, new_name: str) -> None:
        raise NotImplementedError

    def delete_old_backups(self, preset: Preset) -> None:
        raise NotImplementedError

    def get_backups(self, preset: Preset) -> None:
        raise NotImplementedError