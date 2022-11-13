from pathlib import Path

from .preset import Preset
from .backup import Backup

class CommandHandler:
    def list_presets(self, config_path: Path) -> list[Preset]:
        raise NotImplementedError

    def get_preset(self, config_path: Path, name: str):
        raise NotImplementedError

    def save_preset(self, preset: Preset):
        raise NotImplementedError
    
    def delete_preset(self, config_path: Path, preset: Preset) -> Preset:
        raise NotImplementedError

    def list_backups(self, preset: Preset) -> list[Backup]:
        raise NotImplementedError

    def create_backup(self, preset: Preset) -> Backup:
        raise NotImplementedError

    def delete_backup(self, backup: Backup) -> Backup:
        raise NotImplementedError

    def restore_backup(self, preset: Preset, backup: Backup) -> Backup:
        raise NotImplementedError