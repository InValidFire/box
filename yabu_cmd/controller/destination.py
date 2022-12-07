from pathlib import Path

VALID_FILE_FORMATS = ['zip']

__all__ = ['Destination']

class Destination:
    def __init__(self, path: Path, date_format: str = "%d_%m_%y__%H%M%S", name_separator: str = "-", max_backup_count: int = 3, file_format: str = "zip"):
        self.path = path
        self.date_format = date_format
        self.name_separator = name_separator  # separates the original file name from the date in the archive name
        self.max_backup_count = max_backup_count
        self.file_format = file_format

    def __eq__(self, other_destination) -> bool:
        if isinstance(other_destination, Destination):
            if self.path != other_destination.path:
                return False
            if self.date_format != other_destination.date_format:
                return False
            if self.name_separator != other_destination.name_separator:
                return False
            if self.max_backup_count != other_destination.max_backup_count:
                return False
            if self.file_format != other_destination.file_format:
                return False
        return True

    def __str__(self) -> str:
        return str(self.path)

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
    def name_separator(self) -> str:
        return self._name_separator

    @name_separator.setter
    def name_separator(self, new_separator):
        if not isinstance(new_separator, str):
            raise TypeError(new_separator)
        else:
            self._name_separator = new_separator

    @property
    def file_format(self):
        return self._file_format

    @file_format.setter
    def file_format(self, new_file_format):
        if new_file_format not in VALID_FILE_FORMATS:
            raise ValueError(new_file_format)
        else:
            self._file_format = new_file_format