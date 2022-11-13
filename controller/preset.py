from pathlib import Path

from .backup import Backup

class Preset:
    def __init__(self, name: str, date_format: str = "%d_%m_%y__%H%M%S", separator: str = "-"):
        self._targets: list[Path] = []
        self._destinations: list[Path] = []
        self.name = name
        self.date_format = date_format
        self.separator = separator

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, new_name) -> None:
        if not isinstance(new_name, str):
            raise TypeError(new_name)
        else:
            self.name = new_name

    @property
    def date_format(self) -> str:
        return self._date_format

    @date_format.setter
    def date_format(self, new_date_format: str):
        if not isinstance(new_date_format, str):
            raise TypeError(new_date_format)
        else:
            self._date_format = new_date_format

    @property
    def separator(self) -> str:
        return self._separator

    @separator.setter
    def separator(self, new_separator):
        if not isinstance(new_separator, str):
            raise TypeError(new_separator)
        else:
            self._separator = new_separator

    def add_target(self, target_path: Path) -> None:
        raise NotImplementedError

    def add_destination(self, destination_path: Path) -> None:
        raise NotImplementedError

    def remove_target(self, target_path: Path) -> None:
        raise NotImplementedError

    def remove_destination(self, destination_path: Path) -> None:
        raise NotImplementedError

    def create_backup(self) -> Backup:
        raise NotImplementedError

    def restore_backup(self, backup: Backup) -> None:
        raise NotImplementedError

    def get_backups(self) -> list[Backup]:
        raise NotImplementedError

    def get_latest_backup(self) -> Backup:
        raise NotImplementedError