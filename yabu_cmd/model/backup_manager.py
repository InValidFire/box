from pathlib import Path
from typing import Generator
from itertools import product
from datetime import datetime
from zipfile import ZipFile, ZIP_DEFLATED
import json
import hashlib

from ..controller.backup import Backup
from ..controller.preset import Preset
from ..controller.destination import Destination
from ..controller.progress_info import ProgressInfo

from ..exceptions import (
    YabuException,
    FormatException,
    BackupHashException,
    TargetNotFoundException,
    DestinationNotFoundException,
    BackupAbortedException,
)

__all__ = ["BackupManager"]


def count_files(path: Path, files_only=False):
    if not path.is_dir():
        raise ValueError(path)
    count = 0
    for _ in path.glob("**/*"):
        if files_only and _.is_file():
            count += 1
        elif not files_only:
            count += 1
    return count


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

    def _create_metafile(
        self,
        target: Path,
        destination: Destination,
        content_hash: str,
    ) -> str:
        """Create the metafile of a backup. Stores the backup's target source,
        the name_separator, the date_format, and the content_hash. All of this
        allows the backup to identify itself and present itself correctly to
        the user.

        This method does not write the metafile to the archive.
        That is done in the create_backup method.

        Args:
            target (Path): The target the backup was created from.
            destination (Destination): The destination path.
                Used to fetch metadata.
            content_hash (str): The hash of the backup's contents.

        Returns:
            str: The contents of the metafile.
        """
        metadata = {
            "target": str(target),
            "name_separator": destination.name_separator,
            "date_format": destination.date_format,
            "content_hash": content_hash,
            "content_type": get_content_type(target),
        }
        return json.dumps(metadata, indent=4)

    def _create_zip_archive(
        self,
        archive_name: str,
        target: Path,
        destination: Destination,
        metafile_str: str,
    ) -> Generator[Path | ProgressInfo, None, None]:
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
        try:
            with ZipFile(archive_path, mode="w", compression=ZIP_DEFLATED) as zip_file:
                if target.is_dir():
                    file_count = (
                        count_files(target) + 1
                    )  # adding one for the .yabu.meta
                    yield ProgressInfo(0, msg=f"Zipping {target}", total=file_count)
                    for item in target.glob("**/*"):
                        yield ProgressInfo(
                            msg=f"Zipping {target.name} | {item.relative_to(target)}"
                        )
                        zip_file.write(item, item.relative_to(target))
                elif target.is_file():
                    file_count = 2
                    yield ProgressInfo(0, msg=f"Zipping {target}", total=file_count)
                    zip_file.write(target, target.relative_to(target.parent))
                    yield ProgressInfo(msg=f"Zipping {target}")
                else:
                    raise ValueError(target)
                zip_file.writestr(".yabu.meta", metafile_str)
                yield ProgressInfo(msg="Zipping .yabu.meta")
        finally:
            yield archive_path

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
        for backup in destination.get_backups(target):
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
            backup.delete()

    def create_md5_hash(
        self, target: Path
    ) -> Generator[ProgressInfo | str, None, None]:
        md5_hash = hashlib.md5()
        if target.is_dir():
            file_count = count_files(target, files_only=True)
            yield ProgressInfo(count=0, msg="Checking MD5 Hash", total=file_count)
            for item in target.glob("**/*"):
                if item.is_dir():  # can't read bytes of a folder.
                    continue
                md5_hash.update(item.read_bytes())
                yield ProgressInfo(msg="Checking MD5 Hash")
        elif target.is_file():
            md5_hash.update(target.read_bytes())
            yield ProgressInfo(count=1, msg="Checking MD5 Hash", total=1)
        else:
            raise ValueError(target)
        yield md5_hash.hexdigest()

    def create_backups(
        self,
        preset: Preset,
        force=False,
        keep=False,
    ) -> Generator[Backup | YabuException | ProgressInfo, None, None]:
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
            md5_hash = None
            for i in self.create_md5_hash(target):
                if isinstance(i, ProgressInfo):
                    yield i
                elif isinstance(i, str):
                    md5_hash = i
            latest_backup = self.get_latest_backup(destination, target)
            metafile_str = self._create_metafile(target, destination, md5_hash)
            if not force and latest_backup is not None:
                if latest_backup.content_hash == md5_hash:
                    yield BackupHashException(
                        msg=latest_backup.path, target=target, destination=destination
                    )
                    continue
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
            try:
                if (
                    destination.file_format == "zip"
                ):  # allows us to support more formats later
                    for item in self._create_zip_archive(
                        archive_name, target, destination, metafile_str
                    ):
                        if isinstance(
                            item, ProgressInfo
                        ):  # passes zip progress to the view.
                            yield item
                        elif isinstance(item, Path):
                            archive_path = item
                else:
                    yield FormatException(
                        msg=destination.file_format,
                        target=target,
                        destination=destination,
                    )
                    continue
                if not keep:
                    self._delete_old_backups(target, destination)
                yield Backup.from_file(archive_path)
            except KeyboardInterrupt:
                archive_path.unlink()
                yield BackupAbortedException(
                    "The backup was aborted", target, destination
                )
            except Exception:  # keep from storing backups that failed for other means.
                archive_path.unlink()
                raise

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
        only get all backups of the target. Backups are sorted in ascending
        order.

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
            return source.get_backups()
        elif isinstance(source, Destination) and target is not None:
            return source.get_backups(target)
        elif isinstance(source, Preset) and target is None:
            backups: list[Backup] = []
            for preset_destination in source._destinations:
                backups += preset_destination.get_backups()
            backups.sort(key=lambda x: x.date)
            return backups
        elif isinstance(source, Preset) and target is not None:
            for preset_destination in source._destinations:
                backups += preset_destination.get_backups(target)
            backups.sort(key=lambda x: x.date)
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
