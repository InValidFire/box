from pathlib import Path

import json
from jsonschema import validate, ValidationError

from ..controller.preset import Preset
from ..controller.preset import Destination
from ..exceptions.exceptions import InvalidPresetConfig
from .destination_manager import DestinationManager
from ..controller.destination import VALID_FILE_FORMATS

__all__ = ["PresetManager"]

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
    def default(self, o):
        if isinstance(o, Preset):
            return {f"{o.name}": {"targets": o.targets, "destinations": o.destinations}}
        if isinstance(o, Destination):
            return {"path": o.path, "max_backup_count": o.max_backup_count, "file_format": o.file_format, "date_format": o.date_format, "name_separator": o.name_separator}
        return json.JSONEncoder.default(self, o)

class PresetManager:
    def __new__(cls, file_path: Path, *args, **kwargs):  # file_path arg is given to remove from *args and avoid passing it to super()
        if not hasattr(cls, 'instance'):
            cls.instance = super(PresetManager, cls).__new__(cls, *args, **kwargs)
        return cls.instance

    def __init__(self, file_path: Path | str):
        self.file_path = file_path
        try:  # validate the JSON against the schema
            with self.file_path.open("r") as fp:
                presets_data = json.load(fp)
            validate(presets_data, schema=schema)
            self.format = presets_data['format']
        except json.JSONDecodeError as e:
            raise InvalidPresetConfig("JSON file could not be decoded. Is the format correct?")
        except ValidationError as e:
            raise InvalidPresetConfig("JSON file does not match schema. Do you have all required values?")

    def __getitem__(self, key) -> Preset:
        for preset in self.get_presets():
            if preset.name == key:
                return preset
        raise KeyError(key)

    @property
    def file_path(self) -> Path:
        return self._file_path

    @file_path.setter
    def file_path(self, new_path: Path) -> None:
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
        presets = []
        with self.file_path.open("r") as fp:
            presets_data = json.load(fp)
        for preset_name in presets_data['presets']:
            preset_data = presets_data['presets'][preset_name]
            preset = Preset(preset_name)
            for target in preset_data['targets']:
                preset.targets.append(Path(target))
            destination_manager = DestinationManager()
            for destination in preset_data['destinations']:
                destination = destination_manager.get_destination(destination)
                preset.destinations.append(destination)
            presets.append(preset)
        return presets

    def get_preset(self, name: str) -> Preset:
        return self.__getitem__(name)

    def delete_preset(self, preset: Preset) -> None:
        presets = self.get_presets()
        presets.remove(preset)
        with self.file_path.open("w+") as fp:
            json.dump(presets, fp, cls=PresetEncoder)

    def save_preset(self, preset: Preset) -> None:
        raise NotImplementedError