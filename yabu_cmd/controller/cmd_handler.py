from pathlib import Path
from ..model.preset_manager import PresetManager
from .preset import Preset
from .backup import Backup
from ..model.backup_manager import BackupManager

from ..exceptions import PresetNotFoundException, UnsupportedFormatException, BackupHashException, TargetNotFoundException, DestinationNotFoundException

__all__ = ['CommandHandler']

class CommandHandler:
    def __init__(self, config_path: Path | str) -> None:
        self.config_path = config_path
        
    def list_presets(self) -> list[Preset]:
        output = ""
        try:
            preset_manager = PresetManager(self.config_path)
            for preset in preset_manager.get_presets():
                output += str(preset)
        except FileNotFoundError:
            output += f"Uh-Oh! Your config file appears to be missing: '{self.config_path}'"
        except ValueError:
            output += f"The path exists, it doesn't seem to be a .json file though: '{self.config_path}'"
        return output

    def save_preset(self, preset: str):
        raise NotImplementedError
    
    def delete_preset(self, preset: str) -> Preset:
        raise NotImplementedError

    def list_backups(self, preset: str) -> list[Backup]:
        raise NotImplementedError

    def create_backups(self, preset_name: str, force: bool, keep: bool) -> Backup:
        output = ""
        try:
            backup_manager = BackupManager()
            preset_manager = PresetManager(self.config_path)
            preset = preset_manager[preset_name]
        except PresetNotFoundException:
            output += f"The requested preset '{preset_name}' was not found."

        output += "The following backups were created:\n"
        try:
            for backup in backup_manager.create_backups(preset, force=force, keep=keep):
                output += str(backup) + "\n"
        except TargetNotFoundException as e:
            output += f"Backup Failed:\n\tTarget not found:\n\tTarget: {e.target}\n\tDestination: {e.destination}\n"
        except DestinationNotFoundException as e:
            output += f"Backup Failed:\n\tDestination not found:\n\tTarget: {e.target}\n\tDestination: {e.destination}\n"
        except BackupHashException as e:
            output += f"Backup Failed:\n\tBackup hash matched latest backup in destination path.\n\tTarget: {e.target}\n\tDestination: {e.destination}\n"
        except UnsupportedFormatException as e:
            output += f"Backup Failed:\n\tBackup format unsupported\n\tTarget: {e.target}\n\Destination: {e.destination}\n"
        return output

    def delete_backup(self, backup: str) -> Backup:
        raise NotImplementedError

    def restore_backup(self, preset: str, backup: str) -> Backup:
        raise NotImplementedError