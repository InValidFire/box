from pathlib import Path
from datetime import datetime

from .destination import Destination

__all__ = ["Preset"]


class Preset:
    def __init__(self, name: str):
        self._targets: list[Path] = []
        self._destinations: list[Destination] = []
        self.name = name

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
