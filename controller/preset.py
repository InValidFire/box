from pathlib import Path

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
        output += "Targets:" + '\n\t\t- '.join([str(x) for x in self._targets])
        output += "Destinations:" + '\n\t\t- '.join([str(x) for x in self._destinations])
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