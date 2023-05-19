import json
from dataclasses import dataclass
from pathlib import Path
from datetime import datetime

from zipfile import ZipFile, BadZipFile

from .exceptions import NotABackupException, FormatException, ContentTypeException

__all__ = ["Backup"]


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


@dataclass
class Backup:
    name: str = None
    path: Path = None
    date_format: str = None
    name_separator: str = None
    target: Path = None
    date: datetime = None
    content_hash: str = None
    content_type: str = None

    def __str__(self) -> str:
        output = "Backup:"
        output += f"\n\tname: {self.name}"
        output += f"\n\ttarget: {self.target}"
        output += f"\n\tpath: {self.path}"
        output += f"\n\tdate: {self.date}"
        return output

    @staticmethod
    def extract_zip_archive(archive_path: Path, destination_path: Path):
        """Extract a zip archive at the given path to the destination path.

        Args:
            archive_path (Path): The path to the zip archive.
            destination_path (Path): The destination to extract the archive in.
        """
        zf = ZipFile(archive_path)
        zf.extractall(destination_path)

    @staticmethod
    def restore_zip_archive(backup: 'Backup', target: Path):
        """Restore a zip backup to a target path.

        Args:
            backup (Backup): The backup to restore.
            target (Path): The target to restore to.
        """
        Backup.extract_zip_archive(backup.path, target)
        target.joinpath(".box.meta").unlink()

    @classmethod
    def _load_zip(cls, file_path: Path):
        try:
            with ZipFile(file_path, "r") as zip_file:
                if ".box.meta" not in zip_file.namelist():
                    raise NotABackupException(file_path)
                metafile = zip_file.read(".box.meta").decode("utf-8")
                metafile = json.loads(metafile)

                name_separator = metafile['name_separator']
                date_format = metafile['date_format']
                target = Path(metafile['target'])
                content_hash = metafile['content_hash']
                content_type = metafile['content_type']
                name_str = file_path.stem.split(name_separator)[0]
                date_str = file_path.stem.split(name_separator)[1]
                date = datetime.strptime(date_str, date_format)

                backup_path = file_path.absolute()
                return cls(name_str, backup_path, date_format, name_separator, target, date, content_hash, content_type)
        except BadZipFile as e:
            raise FormatException(file_path.suffix) from e

    @classmethod
    def from_file(cls, file_path: Path):
        if file_path.suffix == ".zip":
            return cls._load_zip(file_path)
        else:
            raise FormatException(file_path.suffix)

    @staticmethod
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

    def delete(self):
        self.path.unlink()

    def restore(self, target: Path = None) -> None:
        """Restore the backup to the given target path.

        Args:
            target (Path, optional): The target path to restore the backup to.
                If no target is given, the backup's target is used.

        Raises:
            FileNotFoundError: If the target path's parent does not exist.
                This prevents accidentally making new directory trees.
            ContentTypeException: If you are trying to restore a folder
                backup to a file target, or vice-versa.
            Also raised if the content type is not expected.
            FormatException: If the backup's format is not supported.
        """
        if target is None:
            target = self.target
        if not target.parent.exists():
            raise FileNotFoundError(target.parent)
        if (target.is_dir() and self.content_type == "file") or (
            target.is_file() and self.content_type == "folder"
        ):
            raise ContentTypeException(
                f"The backup content type '{self.content_type}' does not match the target Type."
            )
        if self.content_type == "folder":
            if target.exists():
                rmdir(target)
            target.mkdir()
            if (
                self.path.suffix == ".zip"
            ):  # allows us to support multiple formats later. :)
                self.restore_zip_archive(self, target)
            else:
                raise FormatException(self.path.suffix)
        elif self.content_type == "file":
            if self.path.suffix == ".zip":
                target.unlink(missing_ok=True)
                self.restore_zip_archive(self, target.parent)
            else:
                raise FormatException(self.path.suffix)
        else:
            raise ContentTypeException(
                f"The backup content type '{self.content_type}' is not expected."
            )
