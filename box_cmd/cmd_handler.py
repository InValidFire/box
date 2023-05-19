from pathlib import Path

from typing import Generator

from .preset import Preset
from .backup import Backup
from .progress_info import ProgressInfo
from .destination import Destination

from .exceptions import BoxException, TargetMatchException

__all__ = ["CommandHandler"]


class CommandHandler:
    def __init__(self, config_path: Path | str) -> None:
        if isinstance(config_path, str):
            config_path = Path(config_path)
        Preset.load_file(config_path)

    def list_presets(self) -> list[Preset]:
        """Return a list of presets loaded from the PresetManager's config file.

        Returns:
            list[Preset]: The list of presets.
        """
        presets = Preset.get_presets()
        return presets

    def get_preset(self, preset_name: str) -> Preset:
        """Return a preset from the PresetManager.

        Args:
            preset_name (str): The name of the preset to retrieve.

        Returns:
            Preset: The preset object.
        """
        return Preset.get_preset(preset_name)

    def get_preset_targets(self, preset_name: str) -> list[Path]:
        """Return the list of targets from the preset of the given name.

        Args:
            preset_name (str): The name of the preset to get targets for.

        Returns:
            list[Path]: The list of target paths.
        """
        preset = Preset.get_preset(preset_name)
        return preset._targets.copy()

    def list_backups(self, location: str | Path, file_format="zip") -> list[Backup]:
        """List the backups found in the given location.

        Args:
            location (str | Path): The location to search for backups.
                Can either be a preset name, or a directory path.
            file_format (str, optional): The file format backups are
                saved in. Defaults to "zip".

        Returns:
            list[Backup]: The list of backups found in the location.
        """
        if isinstance(location, str):
            preset = Preset.get_preset(location)
            return preset.get_backups()
        if isinstance(location, Path):
            destination = Destination(
                location, file_format=file_format
            )  # convert location path to a destination object.
            return destination.get_backups()

    def create_backups(
        self, preset_name: str, force: bool, keep: bool
    ) -> Generator[Backup | BoxException | ProgressInfo, None, None]:
        """Create backups of all targets in the preset.
        A backup is stored in each destination following any destination specific
        settings.

        Created backups are only stored if the content hash of the backup does
        not match the most recent backup's content hash. This prevents storing
        of duplicate backups if nothing changed. This behaviour can be disabled
        with the `force` argument.

        Once the amount of backups surpasses the max_backup_count for the destination,
        they are deleted in a rotating fashion. The oldest backups are deleted first
        until the amount of backups in the destination is equal to the max_backup_count.
        This behaviour can be disabled with the `keep` argument.

        Args:
            preset_name (str): The name of the preset.
            force (bool): If true, the backup process will create a backup even if the
                hash check fails.
            keep (bool): If true, the backup process will not delete old backups.

        Yields:
            Backup: the backup created.
            BoxException: any exceptions raised from failed backups.
            ProgressInfo: updates to the backup progress from the model.
        """
        preset: Preset = Preset.get_preset(preset_name)
        for item in preset.create_backups(force=force, keep=keep):
            yield item

    def delete_backup(self, backup_path: Path) -> None:
        """Delete a backup matching the given file path.

        Args:
            backup_path (Path): The file path of the backup to delete.
        """
        backup = Backup.from_file(backup_path)
        backup.delete()

    def restore_backup(self, location: str | Path, backup: Backup):
        """Restore the given backup to its target path.

        If the location argument is a string, a preset will be fetched from
        the PresetManager, and if the backup target is found in the preset's
        targets the backup will be restored.

        If the location arguement is a Path object, the backup will be
        restored to the given path.

        Args:
            location (str | Path): The location to restore the backup to.
                Either a preset name, or a directory path.
            backup (Backup): The backup to restore.

        Raises:
            TargetMatchException: If the backup's target is not found in the
                preset's targets.
            TypeError: If the given location is neither a path or a string.
        """
        if isinstance(location, str):  # get the preset from the preset name
            preset = Preset.get_preset(location)
            if backup.target in preset._targets:
                backup.restore()
            else:
                raise TargetMatchException(preset, backup.target)
        elif isinstance(location, Path):
            backup.restore(location)
        else:
            raise TypeError(location)
