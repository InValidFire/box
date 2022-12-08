from pathlib import Path

from ..model.preset_manager import PresetManager
from .preset import Preset
from .backup import Backup
from .destination import Destination
from ..model.backup_manager import BackupManager

from ..exceptions import YabuException, TargetMatchException

__all__ = ['CommandHandler']


class CommandHandler:
    def __init__(self, config_path: Path | str) -> None:
        self.config_path = config_path
        

    def list_presets(self) -> list[Preset]:
        """Return a list of presets loaded from the PresetManager's config file..

        Returns:
            list[Preset]: The list of presets.
        """
        preset_manager = PresetManager(self.config_path)
        return preset_manager.get_presets()


    def get_preset(self, preset_name: str) -> Preset:
        """Return a preset from the PresetManager.

        Args:
            preset_name (str): The name of the preset to retrieve.

        Returns:
            Preset: The preset object.
        """
        preset_manager = PresetManager(self.config_path)
        return preset_manager.get_preset(preset_name)


    def get_preset_targets(self, preset_name: str) -> list[Path]:
        """Return the list of targets from the preset of the given name.

        Args:
            preset_name (str): The name of the preset to get targets for.

        Returns:
            list[Path]: The list of target paths.
        """
        preset_manager = PresetManager(self.config_path)
        return preset_manager[preset_name]._targets.copy()


    def list_backups(self, location: str | Path, file_format = "zip") -> list[Backup]:
        """List the backups found in the given location.

        Args:
            location (str | Path): The location to search for backups. Can either be a preset name, or a directory path.
            file_format (str, optional): The file format backups are saved in. Defaults to "zip".

        Returns:
            list[Backup]: The list of backups found in the location.
        """
        backup_manager = BackupManager()
        if isinstance(location, str):
            preset_manager = PresetManager(self.config_path)
            location = preset_manager.get_preset(location)
        if isinstance(location, Path):
            location = Destination(location, file_format=file_format)  # convert location path to a destination object.
        return backup_manager.get_backups(location)


    def create_backups(self, preset_name: str, force: bool, keep: bool) -> list[Backup | YabuException]:
        """Create backups of all targets in the preset. 
        A backup is stored in each destination following any destination specific settings.

        Created backups are only stored if the content hash of the backup does not match the most recent backup's content hash.
        This prevents storing of duplicate backups if nothing changed. This behaviour can be disabled with the `force` argument.

        Once the amount of backups surpasses the max_backup_count for the destination, they are deleted in a rotating fashion.
        The oldest backups are deleted first until the amount of backups in the destination is equal to the max_backup_count.
        This behaviour can be disabled with the `keep` argument.

        Args:
            preset_name (str): The name of the preset.
            force (bool): If true, the backup process will create a backup even if the hash check fails.
            keep (bool): If true, the backup process will not delete old backups.

        Yields:
            Generator[Backup | Exception, None, None]: _description_
        """
        backup_manager = BackupManager()
        preset_manager = PresetManager(self.config_path)
        preset = preset_manager[preset_name]
        backups: list[Backup | YabuException] = []
        for backup in backup_manager.create_backups(preset, force=force, keep=keep):
            backups.append(backup)
        return backups


    def delete_backup(self, backup_path: Path) -> None:
        """Delete a backup matching the given file path.

        Args:
            backup_path (Path): The file path of the backup to delete.
        """
        backup_manager = BackupManager()
        backup = backup_manager.get_backup_from_file(backup_path)
        backup_manager.delete_backup(backup)


    def restore_backup(self, location: str | Path, backup: Backup):
        """Restore the given backup to its target path. 
        
        If the location argument is a string, a preset will be fetched from the PresetManager, 
        and if the backup target is found in the preset's targets the backup will be restored.
        
        If the location arguement is a Path object, the backup will be restored to the given path.

        Args:
            location (str | Path): The location to restore the backup to. Either a preset name, or a directory path.
            backup (Backup): The backup to restore.

        Raises:
            TargetMatchException: If the backup's target is not found in the preset's targets.
            TypeError: If the given location is neither a path or a string.
        """
        backup_manager = BackupManager()
        if isinstance(location, str):  # get the preset from the preset name
            preset_manager = PresetManager(self.config_path)
            preset = preset_manager.get_preset(location)
            if backup.target in preset._targets:
                backup_manager.restore_backup(backup.target, backup)
            else:
                raise TargetMatchException(preset, backup.target)
        elif isinstance(location, Path):
            backup_manager.restore_backup(location, backup)
        else:
            raise TypeError(location)
