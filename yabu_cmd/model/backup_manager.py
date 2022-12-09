from pathlib import Path
from typing import Generator
from itertools import product
from datetime import datetime
from zipfile import ZipFile, ZIP_LZMA
import json
import hashlib

from ..controller.backup import Backup
from ..controller.preset import Preset
from ..controller.destination import Destination

from ..exceptions import (
    YabuException,
    FormatException,
    NotABackupException,
    BackupHashException,
    TargetNotFoundException,
    DestinationNotFoundException,
    ContentTypeException,
)

__all__ = ["BackupManager"]


def extract_zip_archive(archive_path: Path, destination_path: Path):
    """Extract a zip archive at the given path to the destination path.

    Args:
        archive_path (Path): The path to the zip archive.
        destination_path (Path): The destination to extract the archive in.
    """
    zf = ZipFile(archive_path)
    zf.extractall(destination_path)


def restore_zip_archive(backup: Backup, target: Path):
    """Restore a zip backup to a target path.

    Args:
        backup (Backup): The backup to restore.
        target (Path): The target to restore to.
    """
    extract_zip_archive(backup.path, target)
    target.joinpath(".yabu.meta").unlink()


def rmdir(path: Path):
    """Recursively remove a directory and its contents.

    Args:
        path (Path): The path to target.

    Raises:
        ValueError: If the path is not a directory.
    """
    if not path.is_dir():
        raise ValueError(path)
    for file in path.iterdir():
        if file.is_file():
            file.unlink()
        if file.is_dir():
            rmdir(file)
    path.rmdir()


def get_content_type(target: Path) -> str:
    """Get the content type of a target path in string format.

    Args:
        target (Path): The target path.

    Raises:
        ValueError: If the target path is neither a file or folder.

    Returns:
        str: The content type.
    """
    if target.is_dir():
        return "folder"
    elif target.is_file():
        return "file"
    else:
        raise ValueError(target)


class BackupManager:
    def __new__(cls):
        if not hasattr(cls, "instance"):
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
                    metafile = zip_file.read(".yabu.meta").decode("utf-8")
                    metadata = json.loads(metafile)

                    name_separator = metadata["name_separator"]
                    date_format = metadata["date_format"]
                    target = Path(metadata["target"])
                    content_hash = metadata["content_hash"]
                    content_type = metadata["content_type"]
                    name_str = file_path.stem.split(name_separator)[0]
                    date_str = file_path.stem.split(name_separator)[1]
                    date = datetime.strptime(date_str, date_format)

                    backup_path = file_path.absolute()
            return Backup(
                name_str,
                backup_path,
                date_format,
                name_separator,
                target,
                date,
                content_hash,
                content_type,
            )

    def _create_metafile(
        self,
        target: Path,
        destination: Destination,
        content_hash: str,
    ) -> Path:
        """Create the metafile of a backup. Stores the backup's target source,
        the name_separator, the date_format, and the content_hash. All of this
        allows the backup to identify itself and present itself correctly to
        the user.

        This method does not write the metafile to the archive.
        That is done in the create_backup method.

        Args:
            target (Path): The target the backup was created from.
            destination (Destination): The destination path.
                The metafile is created here.
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
            "content_hash": content_hash,
            "content_type": get_content_type(target),
        }
        with temp_path.open("w") as fp:
            json.dump(metadata, fp, indent=4)
        return temp_path

    def _create_zip_archive(
        self,
        archive_name: str,
        target: Path,
        destination: Destination,
    ) -> Path:
        """Handle the creation of a zip archive from the target path to the
        destination.

        Args:
            archive_name (str): The name of the archive to be created.
                Excluding the suffix.
            target (Path): The target path.
            destination (Destination): The destination to store the archive.

        Raises:
            ValueError: If the target path is not a file or directory.

        Returns:
            Path: The path of the newly created archive.
        """
        archive_path = destination.path.joinpath(archive_name + ".zip")
        with ZipFile(archive_path, mode="w", compression=ZIP_LZMA) as zip_file:
            if target.is_dir():
                for item in target.glob("**/*"):
                    zip_file.write(item, item.relative_to(target))
            elif target.is_file():
                zip_file.write(target, target.relative_to(target.parent))
            else:
                raise ValueError(target)
        md5_hash = hashlib.md5(archive_path.read_bytes()).hexdigest()
        metafile = self._create_metafile(target, destination, md5_hash)
        with ZipFile(archive_path, "a", compression=ZIP_LZMA) as zip_file:
            zip_file.write(metafile, metafile.relative_to(destination.path))
        metafile.unlink()
        return archive_path

    def _get_backup_date(self, backup: Backup) -> datetime:
        """Internal method to get the backup date from a backup. Used in the
        sorting process of backup lists.

        Args:
            backup (Backup): The backup.
        Returns:
            datetime: The date of the backup.
        """
        return backup.date

    def _get_delete_candidates(
        self,
        target: Path,
        destination: Destination,
    ) -> list[Backup]:
        """Internal method to get all viable delete candidates
        for an input target and destination.

        This method counts all backups found in the destination that were made
        with the given target. If the number of backups matching this criteria
        surpasses the destination's max_backup_count, this method returns a
        list of the oldest backups that could be delete to make the number of
        backups fall within range.

        Args:
            target (Path): The original source path the backups should be made.
            destination (Destination): The destination to get delete
                candidates for.

        Returns:
            list[Backup]: The list of candidates for deletion.
        """
        target_backups: list[Backup] = []
        for backup in self.get_backups(destination):
            if backup.target == target:
                target_backups.append(backup)
        if len(target_backups) > destination.max_backup_count:
            backup_count = len(target_backups) - destination.max_backup_count
            return target_backups[:backup_count]
        else:
            return []

    def _delete_old_backups(self, target: Path, destination: Destination):
        """Internal method to delete old backups for an input target and
        destination. Allows for backup rotation.

        This method deletes all backups returned from
        BackupManager._get_delete_candidates().

        Args:
            target (Path): The target to delete old backups of.
            destination (Destination): The destination to search for backups
                in.
        """
        for backup in self._get_delete_candidates(target, destination):
            self.delete_backup(backup)

    def _get_backups(
        self,
        target: Path,
        destination: Destination,
    ) -> list[Backup]:
        """Get all backups of a specific target found in a destination.

        Args:
            target (Path): The target path.
            destination (Destination): The destination to search.

        Returns:
            list[Backup]: A list containing Backups of the target.
        """
        backups = []
        for backup in self._get_destination_backups(destination):
            if backup.target == target:
                backups.append(backup)
        return backups

    def _get_destination_backups(
        self,
        destination: Destination,
    ) -> list[Backup]:
        """Internal method to get all backups found in a destination,
        regardless of their original source target.

        Args:
            destination (Destination): The destination to get backups from.

        Raises:
            UnsupportedFormatException: If the format loaded in the
                destination is unknown.

        Returns:
            list[Backup]: A list of all backups found in the destination,
                sorted by date in ascending order.
        """
        backups: list[Backup] = []
        if destination.file_format == "zip":
            for path in destination.path.glob("*.zip"):
                backup = self.get_backup_from_file(path)
                backups.append(backup)
        else:
            raise FormatException(destination.file_format)
        backups.sort(key=self._get_backup_date)
        return backups

    def create_backups(
        self,
        preset: Preset,
        force=False,
        keep=False,
    ) -> Generator[Backup | YabuException, None, None]:
        """Trigger backup creation of all available targets in a preset to all
        available destinations in a preset. Automatically rotates backups to
        keep within the max_backup_count specified.

        If `force` is set to
        True, the content hash check will be disabled and duplicate backups
        may be created.

        If `keep` is set to True, the backup rotation will
        be disabled, allowing you to store backups beyond the max_backup_count.

        Args:
            preset (Preset): The preset to trigger backup creation for.
            force (bool, optional): Disable content hash checking and allow
                duplicate backups. Defaults to False.
            keep (bool, optional): Disable backup rotation. Defaults to False.

        Yields:
            UnsupportedFormatException: If the destination's file_format is
                unknown.
            BackupHashException: If the backup's content exactly matches the
                previous backup. The backup will be deleted to save space.
            TargetNotFoundException: If the backup's target could not be found.
            DestinationNotFoundException: If the backup's destination could
                not be found.
            Backup: yields a backup of the target stored in the destination.
        """
        for target, destination in product(preset._targets, preset._destinations):
            latest_backup = self.get_latest_backup(destination, target)
            if not target.exists():
                yield TargetNotFoundException(
                    msg=target, target=target, destination=destination
                )  # cannot raise exceptions or the generator dies. we'll raise them later.
                continue
            if not destination.path.exists():
                yield DestinationNotFoundException(
                    msg=destination.path, target=target, destination=destination
                )
                continue
            archive_name = (
                target.stem
                + destination.name_separator
                + datetime.now().strftime(destination.date_format)
            )
            # allows us to support more formats later. :)
            if destination.file_format == "zip":
                archive_path = self._create_zip_archive(
                    archive_name, target, destination
                )
            else:
                yield FormatException(
                    msg=destination.file_format, target=target, destination=destination
                )
                continue
            new_backup = self.get_backup_from_file(archive_path)
            if not force and latest_backup is not None:
                if latest_backup.content_hash == new_backup.content_hash:
                    new_backup.path.unlink()
                    yield BackupHashException(
                        msg=latest_backup.path, target=target, destination=destination
                    )
                    continue
            if not keep:
                self._delete_old_backups(target, destination)
            yield new_backup

    def restore_backup(self, target: Path, backup: Backup) -> None:
        """Restore a backup to the given target.

        Args:
            target (Path): The target path to restore the backup to.
            backup (Backup): The backup to restore.

        Raises:
            FileNotFoundError: If the target path's parent does not exist.
                This prevents accidentally making new directory trees.
            ContentTypeException: If you are trying to restore a folder
                backup to a file target, or vice-versa.
            Also raised if the content type is not expected.
            FormatException: If the backup's format is not supported.
        """
        if not target.parent.exists():
            raise FileNotFoundError(target.parent)
        if (target.is_dir() and backup.content_type == "file") or (
            target.is_file() and backup.content_type == "folder"
        ):
            raise ContentTypeException(
                f"The backup content type '{backup.content_type}' does not match the target Type."
            )
        if backup.content_type == "folder":
            if target.exists():
                rmdir(target)
            target.mkdir()
            if (
                backup.path.suffix == ".zip"
            ):  # allows us to support multiple formats later. :)
                restore_zip_archive(backup, target)
            else:
                raise FormatException(backup.path.suffix)
        elif backup.content_type == "file":
            if backup.path.suffix == ".zip":
                target.unlink(missing_ok=True)
                restore_zip_archive(backup, target.parent)
            else:
                raise FormatException(backup.path.suffix)
        else:
            raise ContentTypeException(
                f"The backup content type '{backup.content_type}' is not expected."
            )

    def delete_backup(self, backup: Backup) -> None:
        """Delete the given backup.

        Args:
            backup (Backup): The backup to delete.
        """
        backup.path.unlink()

    def delete_old_backups(self, preset: Preset) -> None:
        """Delete the oldest backups in each destination until the number of
        backups is placed within the max_backup_count specified.
        max_backup_count is target specific. ie, if max_backup_count = 3
        for the destination, that's three backups of *each* target.

        Args:
            preset (Preset): preset to determine which backups to delete.
        """
        for target, destination in product(preset._targets, preset._destinations):
            self._delete_old_backups(target, destination)

    def get_delete_candidates(self, preset: Preset) -> list[Backup]:
        """Return a list of candidates for deletion should it be triggered.
        Candidates will be determined by age of the backup, and the oldest
        backups will be eligible first. Candidates will be selected until
        the number of backups is placed within the max_backup_count
        specified for each destination.

        Args:
            preset (Preset): The preset to get deletion candidates for.

        Returns:
            list[Backup]: The list of deletion candidates.
        """
        delete_candidates = []
        for target, destination in product(preset._targets, preset._destinations):
            delete_candidates += self._get_delete_candidates(target, destination)
        return delete_candidates

    def get_backups(
        self, source: Preset | Destination, target: Path = None
    ) -> list[Backup]:
        """Get all backups from the given source. If target is specified,
        only get all backups of the target.

        Args:
            source (Preset | Destination): The source to get backups from.
            target (Path, optional): Target path to limit the backup search.
                Defaults to None.

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
            for preset_target, preset_destination in product(
                source._targets, source._destinations
            ):
                backups += self._get_backups(preset_target, preset_destination)
            backups.sort(key=self._get_backup_date)
            return backups
        elif isinstance(source, Preset) and target is not None:
            for preset_destination in source._destinations:
                backups += self._get_backups(target, preset_destination)
            backups.sort(key=self._get_backup_date)
        else:
            raise TypeError(source)

    def get_latest_backup(
        self, source: Preset | Destination, target: Path = None
    ) -> Backup:
        """Get the latest backup from the given source. If target is specified,
        only get the latest backup of the target.

        If a Preset object is given as the source, get the most recent backup
        of any target it can find in any known destination.
        If a Destination object is given as the source, get the most recent
        backup of any target it can find.

        Args:
            source (Preset | Destination): The source to get the latest backup
                from.
            target (Path, optional): Target path to limit the backup search.
                Defaults to None.

        Returns:
            Backup: The latest backup
        """
        backups = self.get_backups(source, target=target)
        if len(backups) == 0:
            return
        return backups[-1]
