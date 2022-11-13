from pathlib import Path
from dataclasses import dataclass

# TODO: notify user when destination doesn't exist or is not a folder.

@dataclass
class Destination:
    path: Path
    _path: Path
    _max_backup_count: int
    max_backup_count: int = 3

    @property
    def path(self) -> Path:
        return self._path

    @path.setter
    def path(self, new_path: Path) -> Path:
        if not isinstance(new_path, Path):
            raise TypeError(new_path)
        else:
            self._path = new_path

    @property
    def max_backup_count(self):
        return self._max_backup_count

    @max_backup_count.setter
    def max_backup_count(self, new_max_backup_count):
        if not isinstance(new_max_backup_count, int):
            raise TypeError(new_max_backup_count)
        elif not new_max_backup_count > 0:
            raise ValueError(new_max_backup_count)
        else:
            self._max_backup_count = new_max_backup_count