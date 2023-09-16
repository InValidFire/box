from __future__ import annotations

import json
import hashlib

from pathlib import Path
from datetime import datetime
from itertools import product
from typing import Generator
from zipfile import ZipFile, ZIP_DEFLATED

from .destination import Destination, VALID_FILE_FORMATS
from .backup import Backup
from .progress_info import ProgressInfo
from .exceptions import BackupAbortedException, BackupHashException, BoxException, PresetNotFoundException, TargetNotFoundException, DestinationNotFoundException, DestinationLoopException, FormatException, InvalidPresetConfig

from jsonschema import validate, ValidationError

__all__ = ["Preset"]


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


class Preset:
    """Main preset class"""
    def __init__(self, name: str):
        self._targets: list[Path] = []
        self._destinations: list[Destination] = []
        self.name = name

    @staticmethod
    def load_file(config_file: Path) -> list[Preset]:
        return _preset_container.load(config_file)

    @staticmethod
    def get_preset(name: str) -> Preset:
        return _preset_container[name]

    def get_presets() -> list[Preset]:
        return _preset_container.presets

    def __str__(self) -> str:
        output = self.name
        output += "\n\tTargets:"
        for target in self._targets:
            output += f"\n\t\t- {target}"
        output += "\n\tDestinations:"
        for destination in self._destinations:
            output += f"\n\t\t- {destination.path}"
            output += f"\n\t\t\tFile Format: {destination.file_format}"
            output += f"\n\t\t\tMax Backup Count: {destination.max_backup_count}"
            output += f"\n\t\t\tDate Format: {destination.date_format} [{datetime.strftime(datetime.now(), destination.date_format)}]"
            output += f"\n\t\t\tName Separator: {destination.name_separator}"
        return output

    def __eq__(self, other_preset) -> bool:
        if isinstance(other_preset, Preset):
            if self._destinations != other_preset._destinations:
                return False
            if self._targets != other_preset._targets:
                return False
            if self.name != other_preset.name:
                return False
            return True
        return False

    def __repr__(self):
        return f"Preset(name={self.name}, _targets={self._targets}, _destinations={self._destinations})"

    @property
    def name(self) -> str:
        """The name of the preset. Used to identify the preset in the command
        line tool.

        Returns:
            str: The preset name.
        """
        return self._name

    @name.setter
    def name(self, new_name) -> None:
        """The name of the preset. Used to identify the preset in the command
        line tool.

        Args:
            new_name (str): The potential new value for the name.

        Raises:
            TypeError: If the new_name is not a string.
        """
        if not isinstance(new_name, str):
            raise TypeError(new_name)
        else:
            self._name = new_name

    def add_target(self, target: Path):
        """Add a target to the list of targets for the preset.
        This is the recommended way to add targets to the list, as it implements
        type checking to the values before they're added.

        Args:
            target (Path): The target to add to the list.

        Raises:
            TypeError: If the given target is not a Path object.
        """
        if isinstance(target, Path):
            self._targets.append(target)
        else:
            raise TypeError

    def add_destination(self, destination: Destination):
        """Add a destination to the list of destinations for the preset.
        This is the recommended way to add destinations to the list, as it implements
        type checking to the values before they're added.

        Args:
            destination (Destination): The destination to add to the list.

        Raises:
            TypeError: If the given destination is not a Destination object.
        """
        if isinstance(destination, Destination):
            self._destinations.append(destination)
        else:
            raise TypeError(destination)

    def save(self):
        """Save the preset to the config file.

        Args:
            config_file (Path): The path to the config file.
        """
        _preset_container.save(self)

    def delete(self):
        _preset_container.delete_preset(self)

    def remove_target(self, target: Path):
        """Remove a target from the list of targets for the preset.

        Args:
            target (Path): The target path to remove.
        """
        self._targets.remove(target)

    def remove_destination(self, destination: Destination):
        """Remove a Destination from the list of destinations for the preset.

        Args:
            destination (Destination): The Destination object to remove.
        """
        self._destinations.remove(destination)

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
            "content_type": Backup.get_content_type(target),
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
                    )  # adding one for the .box.meta
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
                zip_file.writestr(".box.meta", metafile_str)
                yield ProgressInfo(msg="Zipping .box.meta")
        finally:
            yield archive_path

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
        force=False,
        keep=False,
    ) -> Generator[Backup | BoxException | ProgressInfo, None, None]:
        """Trigger backup creation of all available targets in a preset to all
        available destinations in a preset. Automatically rotates backups to
        keep within the max_backup_count specified.

        If `force` is set to
        True, the content hash check will be disabled and duplicate backups
        may be created.

        If `keep` is set to True, the backup rotation will
        be disabled, allowing you to store backups beyond the max_backup_count.

        Args:
            force (bool, optional): Disable content hash checking and allow
                duplicate backups. Defaults to False.
            keep (bool, optional): Disable backup rotation. Defaults to False.

        Yields:
            ProgressInfo: Contains file progress on backup creation.
            UnsupportedFormatException: If the destination's file_format is
                unknown.
            BackupHashException: If the backup's content exactly matches the
                previous backup. The backup will be deleted to save space.
            TargetNotFoundException: If the backup's target could not be found.
            DestinationNotFoundException: If the backup's destination could
                not be found.
            DestinationLoopException: If the Destination path is contained
                within the target path.
            FormatException: If the destination format is not supported.
            Backup: yields a backup of the target stored in the destination.
        """
        for target, destination in product(self._targets, self._destinations):
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
            md5_hash = None
            for i in self.create_md5_hash(target):
                if isinstance(i, ProgressInfo):
                    yield i
                elif isinstance(i, str):
                    md5_hash = i
            latest_backup = destination.get_latest_backup(target)
            metafile_str = self._create_metafile(target, destination, md5_hash)
            if not force and latest_backup is not None:
                if latest_backup.content_hash == md5_hash:
                    yield BackupHashException(
                        msg=latest_backup.path, target=target, destination=destination
                    )
                    continue
            if target in destination.path.parents or target == destination.path:
                # ensure destination cannot be contained inside a target path.
                yield DestinationLoopException(msg="Destination is contained within the target.", 
                                                target=target, destination=destination)
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

    def get_backups(
        self, target: Path = None
    ) -> list[Backup]:
        """Get all backups from the Preset. If target is specified,
        only get all backups of the target. Backups areS sorted in ascending
        order.

        Args:
            target (Path, optional): Target path to limit the backup search.
                Defaults to None.

        Raises:
            TypeError: If the source is neither a Preset or a Destination.

        Returns:
            list[Backup]: The list of backups.
        """
        backups: list[Backup] = []
        if target is None:
            for preset_destination in self._destinations:
                backups += preset_destination.get_backups()
            backups.sort(key=lambda x: x.date)
        else:
            for preset_destination in self._destinations:
                backups += preset_destination.get_backups(target)
            backups.sort(key=lambda x: x.date)
        return backups

    def get_latest_backup(
        self, target: Path = None
    ) -> Backup:
        """Get the latest backup from the Preset. If target is specified,
        only get the latest backup of the target.

        Args:
            target (Path, optional): Target path to limit the backup search.
                Defaults to None.

        Returns:
            Backup: The latest backup
        """
        backups = self.get_backups(target=target)
        if len(backups) == 0:
            return
        return backups[-1]

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

    def get_delete_candidates(self) -> list[Backup]:
        """Return a list of candidates for deletion should it be triggered.
        Candidates will be determined by age of the backup, and the oldest
        backups will be eligible first. Candidates will be selected until
        the number of backups is placed within the max_backup_count
        specified for each destination.

        Returns:
            list[Backup]: The list of deletion candidates.
        """
        delete_candidates = []
        for target, destination in product(self._targets, self._destinations):
            delete_candidates += self._get_delete_candidates(target, destination)
        return delete_candidates

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

    def delete_old_backups(self) -> None:
        """Delete the oldest backups in each destination until the number of
        backups is placed within the max_backup_count specified.
        max_backup_count is target specific. ie, if max_backup_count = 3
        for the destination, that's three backups of *each* target.
        """
        for target, destination in product(self._targets, self._destinations):
            self._delete_old_backups(target, destination)


# this JSON schema is used to validate the PresetManager config file structure.
schema = {
    "$schema": "http://json-schema.org/draft-06/schema#",
    "$ref": "#/definitions/Root",
    "definitions": {
        "Root": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "format": {"type": "integer"},
                "presets": {
                    "type": "object",
                    "patternProperties": {
                        "^[a-zA-Z0-9_]+$": {"$ref": "#/definitions/Preset"}
                    },
                },
            },
            "required": ["format"],
            "minProperties": 2,
            "title": "Root",
        },
        "Preset": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "targets": {
                    "type": "array",
                    "items": {"type": "string"},
                    "minItems": 1,
                },
                "destinations": {
                    "type": "array",
                    "items": {"$ref": "#/definitions/Destination"},
                    "minItems": 1,
                },
            },
            "required": ["destinations", "targets"],
            "title": "Minecraft",
        },
        "Destination": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "path": {"type": "string"},
                "max_backup_count": {"type": "integer"},
                "file_format": {"type": "string", "enum": VALID_FILE_FORMATS},
                "date_format": {"type": "string"},
                "name_separator": {"type": "string"},
            },
            "required": ["path"],
            "title": "Destination",
        },
    },
}


class PresetEncoder(json.JSONEncoder):
    """
    Handles encoding of Preset objects into JSON formatting.
    """

    def default(self, o):
        if isinstance(o, Preset):
            return {"targets": o._targets, "destinations": o._destinations}
        if isinstance(o, Destination):
            return {
                "path": o.path,
                "max_backup_count": o.max_backup_count,
                "file_format": o.file_format,
                "date_format": o.date_format,
                "name_separator": o.name_separator,
            }
        if isinstance(o, Path):
            return str(o)
        return json.JSONEncoder.default(self, o)


class PresetConfigFile:
    def __init__(self) -> None:
        self._presets: dict[str, Preset] = {}

    @property
    def presets(self):
        return list(self._presets.values())

    def save(self, preset: Preset):
        self._presets[preset.name] = preset
        presets_dict = self._format_presets_dict(self._presets)
        with self.config_file.open("w+") as fp:
            print(json.dumps(presets_dict, cls=PresetEncoder))
            json.dump(presets_dict, fp, cls=PresetEncoder)

    def verify_file(self, config_file: Path):
        try:  # validate the JSON against the schema
            with config_file.open("r") as fp:
                presets_data = json.load(fp)
            validate(presets_data, schema=schema)
        except json.JSONDecodeError:
            raise ValueError(
                "JSON file could not be decoded. Is the format correct?"
            )
        except ValidationError:
            raise InvalidPresetConfig(
                "JSON file does not match schema. Do you have all required values?"
            )

    def _format_presets_dict(self, presets: dict[str, Preset]):
        """Formats the given presets dictionary to the required format.
        Intended to use before dumping dictionary to file.

        Args:
            presets (dict[str, Preset]): The dictionary to format.

        Returns:
            dict: The new formatted dictionary.
        """
        presets_dict = {"format": self.format, "presets": presets}
        return presets_dict

    def load(self, config_file: Path):
        """Internal method to load presets from the config file into a
        dictionary format.

        Returns:
            dict[str, Preset]: The dictionary of Preset objects, with
                the preset name as the key.
        """
        self.verify_file(config_file)
        self.config_file = config_file
        self._presets = {}
        with config_file.open("r") as fp:
            presets_dict = json.load(fp)
            self.format = presets_dict["format"]
        for preset_name in presets_dict["presets"]:
            preset_dict = presets_dict["presets"][preset_name]
            preset = Preset(preset_name)
            for target in preset_dict["targets"]:
                preset.add_target(Path(target))
            for destination in preset_dict["destinations"]:
                destination = Destination.from_dict(destination)
                preset.add_destination(destination)
            self._presets[preset_name] = preset
        return list(self._presets.values())

    def delete_preset(self, preset: Preset) -> None:
        """Delete a preset from the preset config file.

        Args:
            preset (Preset): The preset to remove.

        Raises:
            PresetNotFoundException: If the preset is not found in the config
                file.
        """
        try:
            self._presets.pop(preset.name)
        except KeyError as e:
            raise PresetNotFoundException(preset.name) from e
        presets_dict = self._format_presets_dict(self._presets)
        with self.config_file.open("w+") as fp:
            json.dump(presets_dict, fp, cls=PresetEncoder)

    def __getitem__(self, key: str) -> Preset:
        try:
            return self._presets[key]
        except KeyError as e:
            raise PresetNotFoundException(key) from e


_preset_container = PresetConfigFile()
