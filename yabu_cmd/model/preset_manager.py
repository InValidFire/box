from pathlib import Path

import json
from jsonschema import validate, ValidationError

from ..controller.preset import Preset
from ..controller.preset import Destination
from ..exceptions.exceptions import InvalidPresetConfig, PresetNotFoundException
from .destination_manager import DestinationManager
from ..controller.destination import VALID_FILE_FORMATS

__all__ = ["PresetManager"]

# this JSON schema is used to validate the PresetManager config file structure.
schema = {
    "$schema": "http://json-schema.org/draft-06/schema#",
    "$ref": "#/definitions/Root",
    "definitions": {
        "Root": {
            "type": "object",
            "additionalProperties": False,
			"properties": {
				"format": {
					"type": "integer"
				},
              	"presets": {
                  "type": "object",
                  "patternProperties": {
                  "^[a-zA-Z0-9_]+$": {
                      "$ref": "#/definitions/Preset"
                      }
                  }
                }
			},
            "required": [
                "format"
            ],
            "minProperties": 2,
            "title": "Root"
        },
        "Preset": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "targets": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    },
                    "minItems": 1
                },
                "destinations": {
                    "type": "array",
                    "items": {
                        "$ref": "#/definitions/Destination"
                    },
                    "minItems": 1
                }
            },
            "required": [
                "destinations",
                "targets"
            ],
            "title": "Minecraft"
        },
        "Destination": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "path": {
                    "type": "string"
                },
                "max_backup_count": {
                    "type": "integer"
                },
                "file_format": {
                    "type": "string",
                    "enum": VALID_FILE_FORMATS
                },
                "date_format": {
                    "type": "string"
                },
                "name_separator": {
                    "type": "string"
                }
            },
            "required": [
                "path"
            ],
            "title": "Destination"
        }
    }
}

class PresetEncoder(json.JSONEncoder):
    """
    Handles encoding of Preset objects into JSON formatting.
    """
    def default(self, o):
        if isinstance(o, Preset):
            return {"targets": o._targets, "destinations": o._destinations}
        if isinstance(o, Destination):
            return {"path": o.path, "max_backup_count": o.max_backup_count, "file_format": o.file_format, "date_format": o.date_format, "name_separator": o.name_separator}
        if isinstance(o, Path):
            return str(o)
        return json.JSONEncoder.default(self, o)

class PresetManager:
    """
    Handles the loading and saving of Preset objects to the config file.

    Methods:
        - get_presets(): list[Preset]
        - get_preset(name: str): Preset
        - delete_preset(preset: Preset): None
        - save_preset(preset: Preset): None
    """
    def __new__(cls, file_path: Path, *args, **kwargs):  # file_path arg is given to remove from *args and avoid passing it to super()
        if not hasattr(cls, 'instance'):
            cls.instance = super(PresetManager, cls).__new__(cls, *args, **kwargs)
        return cls.instance

    def __init__(self, config_file: Path | str):
        self.config_file = config_file
        try:  # validate the JSON against the schema
            with self.config_file.open("r") as fp:
                presets_data = json.load(fp)
            validate(presets_data, schema=schema)
            self.format = presets_data['format']
            self._presets = self._get_presets()
        except json.JSONDecodeError as e:
            raise InvalidPresetConfig("JSON file could not be decoded. Is the format correct?")
        except ValidationError as e:
            raise InvalidPresetConfig("JSON file does not match schema. Do you have all required values?")

    def __getitem__(self, key: str) -> Preset:
        """Access the loaded presets in a dictionary-like fashion.

        Args:
            key (str): The name of the preset to return.

        Raises:
            PresetNotFoundException: If the preset is not found.

        Returns:
            Preset: The preset matching the requested name.
        """
        try:
            return self._presets[key]
        except KeyError as e:
            raise PresetNotFoundException(key) from e

    def _format_presets_dict(self, presets: dict[str, Preset]):
        """Formats the given presets dictionary to the required format. Intended to use before dumping dictionary to file.

        Args:
            presets (dict[str, Preset]): The dictionary to format.

        Returns:
            dict: The new formatted dictionary.
        """
        presets_dict = {
            "format": self.format,
            "presets": presets
        }
        return presets_dict

    def _get_presets(self) -> dict[str, Preset]:
        """Internal method to load presets from the config file into a dictionary format.

        Returns:
            dict[str, Preset]: The dictionary of Preset objects, with the preset name as the key.
        """
        presets = {}
        with self.config_file.open("r") as fp:
            presets_dict = json.load(fp)
        for preset_name in presets_dict['presets']:
            preset_dict = presets_dict['presets'][preset_name]
            preset = Preset(preset_name)
            for target in preset_dict['targets']:
                preset.add_target(Path(target))
            destination_manager = DestinationManager()
            for destination in preset_dict['destinations']:
                destination = destination_manager.get_destination(destination)
                preset.add_destination(destination)
            presets[preset.name] = preset
        return presets

    @property
    def config_file(self) -> Path:
        """Getter for the config file.

        Returns:
            Path: Path to the config file.
        """
        return self._file_path

    @config_file.setter
    def config_file(self, new_path: Path) -> None:
        """Setter for the file_path argument. Ensures the path exists, is a file, and has a .json extension.

        Args:
            new_path (Path): The new path to set.

        Raises:
            TypeError: If the new_path is not a pathlib.Path() object.
            FileNotFoundError: If the new_path cannot be found.
            ValueError: If the new_path is not a file or does not have a .json extension.
        """
        if isinstance(new_path, str):
            new_path = Path(new_path)
        if not isinstance(new_path, Path):
            raise TypeError(new_path)
        elif not new_path.exists():
            raise FileNotFoundError(new_path)
        elif new_path.is_file() and new_path.suffix == ".json":
            self._file_path = new_path
        else:
            raise ValueError(new_path)

    def get_presets(self) -> list[Preset]:
        """Getter for loaded presets.

        Returns:
            list[Preset]: a list of presets.
        """
        return list(self._presets.values())

    def get_preset(self, name: str) -> Preset:
        """Get a single preset.

        Args:
            name (str): The name of the preset.

        Returns:
            Preset: The requested preset.
        """
        return self.__getitem__(name)

    def delete_preset(self, preset: Preset) -> None:
        """Delete a preset from the preset config file.

        Args:
            preset (Preset): The preset to remove.

        Raises:
            PresetNotFoundException: If the preset is not found in the config file.
        """
        try:
            self._presets.pop(preset.name)
        except KeyError as e:
            raise PresetNotFoundException(preset.name) from e
        presets_dict = self._format_presets_dict(self._presets)
        with self.config_file.open("w+") as fp:
            json.dump(presets_dict, fp, cls=PresetEncoder)

    def save_preset(self, preset: Preset) -> None:
        """Save a preset to the preset config file.

        Args:
            preset (Preset): The preset to save.
        """
        self._presets[preset.name] = preset
        presets_dict = self._format_presets_dict(self._presets)
        with self.config_file.open("w+") as fp:
            print(json.dumps(presets_dict, cls=PresetEncoder))
            json.dump(presets_dict, fp, cls=PresetEncoder)
