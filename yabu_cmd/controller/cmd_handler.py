from pathlib import Path
from ..model import PresetManager
from .preset import Preset
from .backup import Backup

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

    def get_preset(self, name: str):
        raise NotImplementedError

    def save_preset(self, preset: Preset):
        raise NotImplementedError
    
    def delete_preset(self, preset: Preset) -> Preset:
        raise NotImplementedError

    def list_backups(self, preset: Preset) -> list[Backup]:
        raise NotImplementedError

    def create_backup(self, preset: Preset) -> Backup:
        raise NotImplementedError

    def delete_backup(self, backup: Backup) -> Backup:
        raise NotImplementedError

    def restore_backup(self, preset: Preset, backup: Backup) -> Backup:
        raise NotImplementedError