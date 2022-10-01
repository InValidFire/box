"""
Backup Module:

Classes:
- BackupManager
"""
import hashlib

from datetime import datetime
from pathlib import Path
from zipfile import ZipFile

__all__ = ["BackupManager"]

class BackupManager:
    """
    Facilitates backup creation.

    Methods:
    - create_backup()
    - restore_backup()
    - get_backups()
    - get_backup_date()
    - get_latest_backup()
    - get_delete_candidates()
    - delete_excess_backups()
    """
    def __init__(self, target: Path, storage: Path, date_format: str = "%d_%m_%y__%H%M%S", separator: str = "-") -> None:
        self.target_path = target ## this is a folder. :)
        self.storage = storage
        self.date_format = date_format
        self.separator = separator
        self.storage.mkdir(exist_ok=True, parents=True)

    def __str__(self):
        return f"BackupManager[target={self.target_path}, storage={self.storage}]"

    @property
    def target_path(self) -> Path:
        """
        Target to create backups of. This should be a folder.
        """
        return self._target_path

    @target_path.setter
    def target_path(self, new_path: Path):
        if isinstance(new_path, Path):
            if new_path.exists() and new_path.is_dir():
                self._target_path = new_path
            else:
                raise ValueError(new_path)
        else:
            raise TypeError(new_path)

    @property
    def storage(self) -> Path:
        """
        Storage object to store created backups in.
        """
        return self._storage

    @storage.setter
    def storage(self, new_storage: Path):
        if new_storage.is_dir():
            self._storage = new_storage
        else:
            raise TypeError(new_storage)

    @property
    def date_format(self) -> str:
        """The datetime format string used to date the backups."""
        return self._date_format

    @date_format.setter
    def date_format(self, new_format):
        if isinstance(new_format, str):
            self._date_format = new_format
        else:
            raise TypeError(new_format)

    @property
    def separator(self) -> str:
        """The separator that separates the archive name from the date"""
        return self._separator

    @separator.setter
    def separator(self, new_separator):
        if isinstance(new_separator, str):
            if new_separator not in self.target_path.name and new_separator not in self.date_format:
                self._separator = new_separator
            else:
                raise ValueError(new_separator)
        else:
            raise TypeError(new_separator)

    def create_backup(self, force=False):
        """
        Create a backup of the target folder, stored in the backup storage folder.

        The backup is deleted if the MD5 hash of the new backup matches the latest backup.
        Use force=True to force-create a backup and skip MD5 hash checking.
        """
        date_string = datetime.now().strftime(self.date_format)
        latest_backup = self.get_latest_backup()
        new_backup_name = f"{self.target_path.name}{self.separator}{date_string}.zip"
        new_backup_path = self.storage.joinpath(new_backup_name)
        with ZipFile(new_backup_path, mode="w") as zip_file:
            for item in self.target_path.glob("**/*"):
                zip_file.write(item, item.relative_to(self.target_path))
        if not force and latest_backup is not None:
            new_hash = hashlib.md5(new_backup_path.read_bytes()).hexdigest()
            latest_hash = hashlib.md5(latest_backup.read_bytes()).hexdigest()
            if latest_hash == new_hash:
                new_backup_path.unlink()
                raise FileExistsError(f"This backup matches '{latest_backup.name}'")

    def get_backup_date(self, backup: Path) -> datetime:
        """
        Turns the datetime string in the file name into a datetime object.
        """
        date_string = backup.name.split(self.separator)[1].replace(backup.suffix, "")
        return datetime.strptime(date_string, self.date_format)

    def get_latest_backup(self) -> Path | None:
        """
        Get the latest backup.
        """
        backups = self.get_backups()
        if len(backups) == 0:
            return
        else:
            return self.get_backups()[-1]

    def get_backups(self) -> list[Path]:
        """
        Get all backups found in the given folder, sorted oldest to newest.
        """
        backups = list(self.storage.glob(f"{self.target_path.stem}{self.separator}*.zip"))
        backups.sort(key=self.get_backup_date)
        return backups

    def get_delete_candidates(self, max_backup_count: int) -> list[Path]:
        """
        Get all candidates for deletion with the given max_backup_count.
        If none are available for deletion, returns None.
        """
        backups = self.get_backups()
        if len(backups) < max_backup_count:
            return []
        return backups[:(len(backups)-max_backup_count)]  # returns the oldest excess backups

    def delete_excess_backups(self, max_backup_count: int):
        """Delete all excess backups"""
        for file in self.get_delete_candidates(max_backup_count):
            file.unlink()

    def empty_dir(self, path: Path):
        """Deletes all files and folders inside the given directory.
        If the given path is not a directory, it will raise a TypeError."""
        if not path.is_dir():
            raise TypeError(path)
        for item in path.iterdir():
            if item.is_dir():
                self.empty_dir(item)
            if item.is_file():
                print(f"deleting '{item}'")
                item.unlink()

    def restore_backup(self, backup: Path):
        """Restore to the given backup"""
        target = Path(self.target_path)
        self.empty_dir(target)
        backup_zip = backup.read_zip()
        backup_zip.extractall(target)
        print(f"extracting '{backup_zip.filename}' to '{target}'")
