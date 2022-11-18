from typing import Generator
from pathlib import Path
from itertools import product
from datetime import datetime
from zipfile import ZipFile
import json
import hashlib

from ..controller.backup import Backup
from ..controller.preset import Preset
from ..controller.destination import Destination

from ..exceptions import UnsupportedFormatException, NotABackupException

__all__ = ['BackupManager']

class BackupManager:
    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super().__new__(cls)
        return cls.instance

    def get_backup_from_file(self, file_path: Path) -> Backup:
        """Get a `Backup` object from the requested file path.

        Args:
            file_path (Path): The file path to load a Backup object from.

        Raises:
            NotABackupException: If the metafile cannot be found.

        Returns:
            Backup: The backup object.
        """
        if file_path.suffix == ".zip":
            with ZipFile(file_path, "r") as zip_file:
                if ".yabu.meta" not in zip_file.namelist():
                    raise NotABackupException(zip_file.filename)
                else:
                    metadata = json.loads(zip_file.read(".yabu.meta").decode("utf-8"))
                    date = datetime.strptime(file_path.stem.split(metadata['name_separator'])[1], metadata['date_format'])
            return Backup(file_path.stem.split(metadata['name_separator'])[0], file_path.absolute(), metadata['date_format'], metadata['name_separator'], metadata['target'], date, metadata['content_hash'])

    def _create_metafile(self, target: Path, destination: Destination, content_hash: str) -> Path:
        """Create the metafile of a backup. Stores the backup's target source, the name_separator, the date_format, and the content_hash. 
        All of this allows the backup to identify itself and present itself correctly to the user.

        This method does not write the metafile to the archive. That is done in the create_backup method.

        Args:
            target (Path): The target the backup was created from.
            destination (Destination): The destination path. The meta file is created here.
            content_hash (str): The hash of the backup's contents.

        Returns:
            Path: The path of the metafile.
        """
        temp_path = destination.path.joinpath(".yabu.meta")
        temp_path.touch()
        metadata = {
            "target": str(target),
            "name_separator": destination.name_separator,
            "date_format": destination.date_format,
            "content_hash": content_hash
        }
        with temp_path.open("w") as fp:
            json.dump(metadata, fp)
        return temp_path

    def _create_zip_archive(self, archive_name: str, target: Path, destination: Destination) -> Path:
        """Handle the creation of a zip archive from the target path to the destination.

        Args:
            archive_name (str): The name of the archive to be created. Excluding the suffix.
            target (Path): The target path.
            destination (Destination): The destination to store the archive.

        Raises:
            ValueError: If the target path is not a file or directory.

        Returns:
            Path: The path of the newly created archive.
        """
        archive_path = destination.path.joinpath(archive_name + ".zip")
        with ZipFile(archive_path, mode="w") as zip_file:
            if target.is_dir():
                for item in target.glob("**/*"):
                    zip_file.write(item, item.relative_to(target))
            elif target.is_file():
                zip_file.write(target, target.relative_to(target.parent))
            else:
                raise ValueError(target)  # this should never be raised... **crosses fingers**
        md5_hash = hashlib.md5(archive_path.read_bytes()).hexdigest()
        metafile = self._create_metafile(target, destination, md5_hash)
        with ZipFile(archive_path, "a") as zip_file:
            zip_file.write(metafile, metafile.relative_to(destination.path))
        metafile.unlink()
        return archive_path

    def _get_backup_date(self, backup: Backup) -> datetime:
        """Internal method to get the backup date from a backup. Used in the sorting process of backup lists.

        Args:
            backup (Backup): The backup.
        Returns:
            datetime: The date of the backup.
        """
        return backup.date

    def _get_delete_candidates(self, target: Path, destination: Destination) -> list[Backup]:
        """Internal method to get all viable delete candidates for an input target and destination.

        This method checks all backups found in the destination that were made with the given target.
        If the number of backups matching this criteria surpasses the destination's max_backup_count, this method returns
        a list of the oldest backups that could be deleted to make the number of backups fall within range.

        Args:
            target (Path): The original source path the backups should be made from.
            destination (Destination): The destination to get delete candidates for.

        Returns:
            list[Backup]: _description_
        """
        target_backups: list[Backup] = []
        for backup in self.get_backups(destination):
            if str(backup.target) == str(target):  # allow Path and its children to equate
                target_backups.append(backup)
        if len(target_backups) > destination.max_backup_count:
            return target_backups[:(len(target_backups)-destination.max_backup_count)]
        else:
            return []

    def _delete_old_backups(self, target: Path, destination: Destination):
        """Internal method to delete old backups for an input target and destination.
        Allows for backup rotation.

        This method deletes all backups returned from BackupManager._get_delete_candidates().

        Args:
            target (Path): _description_
            destination (Destination): _description_
        """
        for backup in self._get_delete_candidates(target, destination):
            self.delete_backup(backup)

    def _get_backups(self, target: Path, destination: Destination) -> list[Backup]:
        """Get all backups of a specific target found in a destination.

        Args:
            target (Path): The target path.
            destination (Destination): The destination to search.

        Returns:
            list[Backup]: A list containing Backups of the target.
        """
        backups = []
        for backup in self._get_destination_backups(destination):
            if str(backup.target) == str(target):
                backups.append(backup)
        return backups

    def _get_destination_backups(self, destination: Destination) -> list[Backup]:
        """Internal method to get all backups found in a destination, regardless of their original source target.

        Args:
            destination (Destination): The destination to get backups from.

        Raises:
            UnsupportedFormatException: If the format loaded in the destination is unknown.

        Returns:
            list[Backup]: A list of all backups found in the destination, sorted by date in ascending order.
        """
        backups: list[Backup] = []
        if destination.file_format == "zip":
            for path in destination.path.glob("*.zip"):
                backup = self.get_backup_from_file(path)
                backups.append(backup)
        else:
            raise UnsupportedFormatException(destination.file_format)
        backups.sort(key=self._get_backup_date)
        return backups

    def create_backups(self, preset: Preset, force=False, keep=False) -> Generator[Backup, None, None]:
        """Trigger backup creation of all available targets in a preset to all available destinations in a preset. Automatically rotates backups to keep within the max_backup_count specified.
        \nIf `force` is set to True, the content hash check will be disabled and duplicate backups may be created.
        \nIf `keep` is set to True, the backup rotation will be disabled, allowing you to store backups beyond the max_backup_count.

        Args:
            preset (Preset): The preset to trigger backup creation for.
            force (bool, optional): Disable content hash checking and allow duplicate backups. Defaults to False.
            keep (bool, optional): Disable backup rotation. Defaults to False.

        Raises:
            UnsupportedFormatException: If the destination's file_format is unknown.
            FileExistsError: If the backup's content exactly matches the previous backup. The backup will be deleted to save space.

        Yields:
            Generator[Backup, None, None]: yields a `Backup` object.
        """
        for target, destination in product(preset._targets, preset._destinations):
            latest_backup = self.get_latest_backup(destination, target)
            if not target.exists():  # this target was not available... let's move on.
                continue
            if not destination.path.exists():  # this destination was not available... let's move on.
                continue
            archive_name = target.stem + destination.name_separator + datetime.now().strftime(destination.date_format)
            if destination.file_format == "zip":  # allows us to support more formats later. :)
                archive_path = self._create_zip_archive(archive_name, target, destination)
            else:
                raise UnsupportedFormatException(destination.file_format)
            new_backup = self.get_backup_from_file(archive_path)
            if not force and latest_backup is not None:
                if latest_backup.content_hash == new_backup.content_hash:
                    new_backup.path.unlink()
                    raise FileExistsError(latest_backup.path)
            if not keep:
                self._delete_old_backups(target, destination)
            yield new_backup

    def restore_backup(self, preset: Preset, backup: Backup) -> None:
        raise NotImplementedError

    def delete_backup(self, backup: Backup) -> None:
        """Delete the given backup.

        Args:
            backup (Backup): The backup to delete.
        """
        backup.path.unlink()

    def delete_old_backups(self, preset: Preset) -> None:
        """Delete the oldest backups in each destination until the number of backups is placed within the max_backup_count specified.
        max_backup_count is target specific. ie, if max_backup_count = 3 for the destination, that's three backups of *each* target.

        Args:
            preset (Preset): preset to determine which backups to delete.
        """
        for target, destination in product(preset._targets, preset._destinations):
            self._delete_old_backups(target, destination)

    def get_delete_candidates(self, preset: Preset) -> list[Backup]:
        """Return a list of candidates for deletion should it be triggered.
        Candidates will be determined by age of the backup, and the oldest backups will be eligible first. 
        Candidates will be selected until the number of backups is placed within the max_backup_count specified for each destination.

        Args:
            preset (Preset): The preset to get deletion candidates for.

        Returns:
            list[Backup]: The list of deletion candidates.
        """
        delete_candidates = []
        for target, destination in product(preset._targets, preset._destinations):
            delete_candidates += self._get_delete_candidates(target, destination)
        return delete_candidates

    def get_backups(self, source: Preset | Destination, target: Path = None) -> list[Backup]:
        """Get all backups from the given source. If target is specified, only get all backups of the target.

        Args:
            source (Preset | Destination): The source to get backups from.
            target (Path, optional): Target path to limit the backup search. Defaults to None.

        Raises:
            TypeError: If the source is neither a Preset or a Destination.

        Returns:
            list[Backup]: The list of backups.
        """
        if isinstance(source, Destination) and target is None:
            return self._get_destination_backups(source)
        elif isinstance(source, Destination) and target is not None:
            return self._get_backups(target, source)
        elif isinstance(source, Preset) and target is None:
            backups: list[Backup] = []
            for preset_target, preset_destination in product(source._targets, source._destinations):
                backups += self._get_backups(preset_target, preset_destination)
            backups.sort(key=self._get_backup_date)
            return backups
        elif isinstance(source, Preset) and target is not None:
            for preset_destination in source._destinations:
                backups += self._get_backups(target, preset_destination)
            backups.sort(key=self._get_backup_date)
        else:
            raise TypeError(source)

    def get_latest_backup(self, source: Preset | Destination, target: Path = None) -> Backup:
        """Get the latest backup from the given source. If target is specified, only get the latest backup of the target.

        If a Preset object is given as the source, get the most recent backup of any target it can find in any known destination. 
        If a Destination object is given as the source, get the most recent backup of any target it can find.

        Args:
            source (Preset | Destination): The source to get the latest backup from.
            target (Path, optional): Target path to limit the backup search. Defaults to None.

        Returns:
            Backup: _description_
        """
        backups = self.get_backups(source, target=target)
        if len(backups) == 0:
            return
        return backups[-1]