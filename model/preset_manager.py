from pathlib import Path

from ..controller import Preset

class PresetManager:
    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super().__new__(cls)
        return cls.instance

    def __init__(self, file_path: Path):
        self.file_path = file_path

    @property
    def file_path(self) -> Path:
        return self._file_path

    @file_path.setter
    def file_path(self, new_path: Path) -> None:
        if not isinstance(new_path, Path):
            raise TypeError(new_path)
        elif not new_path.exists():
            raise FileNotFoundError(new_path)
        elif new_path.is_file() and new_path.suffix == ".json":
            self._file_path = new_path
        else:
            raise ValueError(new_path)

    def get_presets(self) -> list[Preset]:
        raise NotImplementedError

    def get_preset(self, name: str) -> Preset:
        raise NotImplementedError

    def delete_preset(self, name: str) -> None:
        raise NotImplementedError

    def save_preset(self, preset: Preset) -> None:
        raise NotImplementedError