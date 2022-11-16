from pathlib import Path

from .destination import Destination
from .backup import Backup

__all__ = ['Preset']

class Preset:
    def __init__(self, name: str):
        self.targets: list[Path] = []
        self.destinations: list[Destination] = []
        self.name = name

    def __str__(self) -> str:
        output = self.name
        output += "Targets:" + '\n\t\t- '.join([str(x) for x in self.targets])
        output += "Destinations:" + '\n\t\t- '.join([str(x) for x in self.destinations])
        return output

    def __eq__(self, other_preset) -> bool:
        if isinstance(other_preset, Preset):
            if self.destinations != other_preset.destinations:
                return False
            if self.targets != other_preset.targets:
                return False
            if self.name != other_preset.name:
                return False
        return True

    def to_dict(self) -> dict:
        output = {}
        

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, new_name) -> None:
        if not isinstance(new_name, str):
            raise TypeError(new_name)
        else:
            self._name = new_name

    def create_backup(self) -> Backup:
        raise NotImplementedError

    def restore_backup(self, backup: Backup) -> None:
        raise NotImplementedError

    def get_backups(self) -> list[Backup]:
        raise NotImplementedError

    def get_latest_backup(self) -> Backup:
        raise NotImplementedError