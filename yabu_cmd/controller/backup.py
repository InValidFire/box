import json
from dataclasses import dataclass
from pathlib import Path
from datetime import datetime

from zipfile import ZipFile, BadZipFile

from ..exceptions import NotABackupException, FormatException

__all__ = ["Backup"]


@dataclass(frozen=True, repr=True)
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

    @classmethod
    def _load_zip(cls, file_path: Path):
        try:
            with ZipFile(file_path, "r") as zip_file:
                if ".yabu.meta" not in zip_file.namelist():
                    raise NotABackupException(file_path)
                metafile = zip_file.read(".yabu.meta").decode("utf-8")
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
