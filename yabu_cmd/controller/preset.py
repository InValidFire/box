from pathlib import Path
from datetime import datetime

from .destination import Destination
from .backup import Backup

__all__ = ['Preset']

class Preset:
    def __init__(self, name: str):
        self._targets: list[Path] = []
        self._destinations: list[Destination] = []
        self.name = name

    def __str__(self) -> str:
        output = self.name
        output += "\n\tTargets:"
        for target in self._targets:
            output += f"\n\t\t - {target}"
        output += "\n\tDestinations:"
        for destination in self._destinations: 
            output += f"\n\t\t- {destination.path}"
            output += f"\n\t\t\tFile Format: {destination.file_format}"
            output += f"\n\t\t\tMax Backup Count: {destination.max_backup_count}"
            output += f"\n\t\t\tDate Format: {destination.date_format} [{datetime.strftime(datetime.now(), destination.date_format)}]"
            output += f"\n\t\t\tName Separator: {destination.name_separator}"
        return output

    def __eq__(self, other_preset) -> bool:
        if isinstance(other_preset, Preset):
            if self._destinations != other_preset._destinations:
                return False
            if self._targets != other_preset._targets:
                return False
            if self.name != other_preset.name:
                return False
        return True

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, new_name) -> None:
        if not isinstance(new_name, str):
            raise TypeError(new_name)
        else:
            self._name = new_name

    def add_target(self, target: Path):
        if isinstance(target, Path):
            self._targets.append(target)
        else:
            raise TypeError

    def add_destination(self, destination: Destination):
        if isinstance(destination, Destination):
            self._destinations.append(destination)
        else:
            raise TypeError(destination)

    def remove_target(self, target: Path):
        self._targets.remove(target)

    def remove_destination(self, destination: Destination):
        self._destinations.remove(destination)

    def create_backup(self) -> Backup:
        raise NotImplementedError

    def restore_backup(self, backup: Backup) -> None:
        raise NotImplementedError

    def get_backups(self) -> list[Backup]:
        raise NotImplementedError

    def get_latest_backup(self) -> Backup:
        raise NotImplementedError