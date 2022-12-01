from pathlib import Path

from ..model.preset_manager import PresetManager
from .preset import Preset
from .backup import Backup
from .destination import Destination
from ..model.backup_manager import BackupManager

from ..exceptions import YabuException, TargetMatchException

__all__ = ['CommandHandler']


class CommandHandler:
    def __init__(self, config_path: Path | str) -> None:
        self.config_path = config_path
        

    def list_presets(self) -> list[Preset]:
        preset_manager = PresetManager(self.config_path)
        return preset_manager.get_presets()


    def get_preset(self, preset_name: str) -> Preset:
        preset_manager = PresetManager(self.config_path)
        return preset_manager.get_preset(preset_name)


    def save_preset(self, preset: str):
        raise NotImplementedError


    def delete_preset(self, preset: str) -> Preset:
        raise NotImplementedError


    def list_backups(self, location: str | Path, file_format = ".zip") -> list[Backup]:
        backup_manager = BackupManager()
        if isinstance(location, str):
            preset_manager = PresetManager(self.config_path)
            location = preset_manager.get_preset(location)
        if isinstance(location, Path):
            location = Destination(location, file_format=file_format)  # convert location path to a destination object.
        return backup_manager.get_backups(location)


    def create_backups(self, preset_name: str, force: bool, keep: bool) -> list[Backup]:
        backup_manager = BackupManager()
        preset_manager = PresetManager(self.config_path)
        preset = preset_manager[preset_name]
        backups: list[Backup | YabuException] = []
        for backup in backup_manager.create_backups(preset, force=force, keep=keep):
            backups.append(backup)
        return backups


    def delete_backup(self, backup_path: Path) -> Backup:
        backup_manager = BackupManager()
        backup = backup_manager.get_backup_from_file(backup_path)
        backup_manager.delete_backup(backup)


    def restore_backup(self, location: str | Path, backup: Backup) -> Backup:
        backup_manager = BackupManager()
        if isinstance(location, str):  # get the preset from the preset name
            preset_manager = PresetManager(self.config_path)
            preset = preset_manager.get_preset(location)
            if backup.target in preset._targets:
                backup_manager.restore_backup(backup.target, backup) 
            else:
                raise TargetMatchException(preset, backup.target, backup.path.parent)
        elif isinstance(location, Path):
            backup_manager.restore_backup(location, backup)
        else:
            raise TypeError(location)
