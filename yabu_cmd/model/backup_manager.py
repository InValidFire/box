from typing import Generator
from pathlib import Path
from itertools import product
from datetime import datetime
from zipfile import ZipFile
import json

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
        if file_path.suffix == ".zip":
            with ZipFile(file_path, "r") as zip_file:
                if ".yabu.meta" not in zip_file.namelist():
                    raise NotABackupException(zip_file.filename)
                else:
                    metadata = json.loads(zip_file.read(".yabu.meta").decode("utf-8"))
            return Backup(file_path.stem.split(metadata['name_separator'])[0], file_path.absolute(), metadata['date_format'], metadata['name_separator'], metadata['target'])

    def _create_metafile(self, target: Path, destination: Destination) -> Path:
        temp_path = destination.path.joinpath(".yabu.meta")
        temp_path.touch()
        metadata = {
            "target": str(target),
            "name_separator": destination.name_separator,
            "date_format": destination.date_format
        }
        with temp_path.open("w") as fp:
            json.dump(metadata, fp)
        return temp_path

    def _create_zip_archive(self, archive_name: str, target: Path, destination: Destination) -> Path:
        archive_path = destination.path.joinpath(archive_name + ".zip")
        with ZipFile(archive_path, mode="w") as zip_file:
            if target.is_dir():
                for item in target.glob("**/*"):
                    zip_file.write(item, item.relative_to(target))
            elif target.is_file():
                zip_file.write(target, target.relative_to(target.parent))
            else:
                raise ValueError(target)  # this should never be raised... **crosses fingers**
            metafile = self._create_metafile(target, destination)
            zip_file.write(metafile, metafile.relative_to(destination.path))
            metafile.unlink()
        return archive_path

    def create_backups(self, preset: Preset, force=False, keep=False) -> Generator[Backup, None, None]:  # TODO: Implement force & keep behaviour.
        for target, destination in product(preset._targets, preset._destinations):
            if not target.exists():
                raise FileNotFoundError(target)
            if not destination.path.exists():
                raise FileNotFoundError(destination.path)
            archive_name = target.stem + destination.name_separator + datetime.now().strftime(destination.date_format)
            if destination.file_format == "zip":  # allows us to support more formats later. :)
                archive_path = self._create_zip_archive(archive_name, target, destination)
            else:
                raise UnsupportedFormatException(destination.file_format)
            yield self.get_backup_from_file(archive_path)

    def restore_backup(self, preset: Preset, backup: Backup) -> None:
        raise NotImplementedError

    def delete_backup(self, backup: Backup) -> None:
        backup.path.unlink()

    def rename_backup(self, backup: Backup, new_name: str) -> None:
        raise NotImplementedError

    def delete_old_backups(self, preset: Preset) -> None:
        raise NotImplementedError

    def get_backups(self, preset: Preset) -> None:
        raise NotImplementedError