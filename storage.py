"""
Storage Module:

Classes:
- StorageRoot
- StorageFolder
- StorageFile
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from collections.abc import Generator

import json
from pathlib import Path
import shutil
from zipfile import ZipFile

__all__ = ['StorageRoot', 'StorageFile', 'StorageFolder']

class StorageException(Exception):
    """Base exception for Storage module"""

class ChildPathError(StorageException):
    """Path is not a child of the StorageRoot"""

class StorageBase(ABC):
    """Base class for all Storage classes, should not be used directly."""
    def __init__(self, path: Path, root: StorageRoot):
        self.path = path
        self.root = root
        if self.root.path not in self.path.parents and self.root.path != self.path:
            raise ChildPathError(f"{self.path} is not a child of {self.root}")

    @property
    def parent(self) -> StorageFolder | None:
        """The parent of the Storage object. StorageRoot will have no parent."""
        if self.root.path not in self.path.parents:
            return None
        return StorageFolder(self.path.parent, self.root)

    @property
    def path(self) -> Path:
        """The filepath of the Storage object."""
        return self._path

    @path.setter
    def path(self, new_path: str | Path):
        if isinstance(new_path, Path):
            self._path = new_path
        else:
            raise TypeError(new_path)

    @property
    def root(self):
        """The StorageRoot object associated with the Storage object."""
        return self._root

    @root.setter
    def root(self, new_root):
        if isinstance(new_root, StorageRoot):
            self._root = new_root
        else:
            raise TypeError(new_root)

    def rename(self, new_name: str | Path):
        """Rename the Storage object."""
        self.path.rename(new_name)

    @abstractmethod
    def delete(self):
        """Delete the Storage object."""

class StorageFolder(StorageBase):
    """A folder located within the Storage system."""
    def __init__(self, path: Path, root: StorageRoot) -> None:
        super().__init__(path, root)
        if not self.path.resolve().exists():
            raise FileNotFoundError(self.path)

    def get_file(self, name: str) -> StorageFile:
        """Get a file located within the StorageFolder"""
        path = self.path.joinpath(name)
        if path.exists() and path.is_file():
            return StorageFile(path, self.root)
        if path.exists() and not path.is_file():
            raise ValueError(f"{path} is a directory.")
        raise FileNotFoundError(self.path.joinpath(name))

    def get_folder(self, name: str) -> StorageFolder:
        """Get a folder located within the StorageFolder."""
        path = self.path.joinpath(name)
        if path.exists():
            return StorageFolder(path, self.root)
        raise FileNotFoundError(path)

    def get_folders(self) -> list[StorageFolder]:
        """Get a list of folders within the StorageFolder."""
        folders = []
        for folder in self.path.iterdir():
            if not folder.is_dir():
                continue
            folders.append(StorageFolder(folder, self.root))
        return folders

    def get_files(self) -> list[StorageFile]:
        """Get a list of files within the StorageFolder."""
        files: list[StorageFile] = []
        for file in self.path.iterdir():
            if not file.is_file():
                continue
            files.append(StorageFile(file, self.root))
        return files

    def iterdir(self):
        """Iterate through the StorageFolder. Operates similarly to the Path.iterdir() method."""
        return iter(self)

    def glob(self, pattern: str) -> Generator[StorageFile | StorageFolder, None, None]:
        """Get a list of files (directories included) that match the given glob pattern."""
        for item in self.path.glob(pattern):
            if item.is_file():
                yield StorageFile(item, self.root)
            if item.is_dir():
                yield StorageFolder(item, self.root)

    def create_folder(self, name) -> StorageFolder:
        """Create a folder within the StorageFolder.
        Returns the new folder's StorageFolder object."""
        folder = self.path.joinpath(name)
        folder.mkdir()
        return StorageFolder(folder, self.root)

    def delete(self):
        """Delete the StorageFolder."""
        if not isinstance(self, StorageRoot):
            shutil.rmtree(self.path)
        else:
            raise ValueError("Cannot delete the StorageRoot.")

    def __str__(self) -> str:
        return str(self.path)

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}("{self.path}")'

    def __iter__(self):
        yield from [StorageFolder(x, self.root) for x in self.path.iterdir()]


class StorageRoot(StorageFolder):
    """The root of a Storage system."""
    def __init__(self, path: Path = Path.home().joinpath(".storage")) -> None:
        if not path.exists() and path == Path.home().joinpath(".storage"):
            path.mkdir()
        super().__init__(path, self)
    

class StorageFile(StorageBase):
    """A file located within the Storage system."""
    def delete(self):
        self.path.unlink()
    
    def read_json(self) -> dict:
        """If the file is a json file, read its data to a dictionary structure and return it."""
        if not self.path.exists():
            return {}
        if self.path.suffix == ".json":
            with self.path.open("r+", encoding="utf-8") as f:
                data = json.load(f)
                return data
        else:
            raise ValueError("File is not in JSON format.")

    def read_zip(self):
        return ZipFile(self.path)

    def read_text(self):
        return self.path.read_text()

    def write(self, data: dict | bytes) -> None:
        """Write a dictionary or bytes object to the file."""
        self.path.touch(exist_ok=True)
        if isinstance(data, dict):
            with self.path.open("w+", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
        elif isinstance(data, bytes):
            self.path.write_bytes(data)

    def __str__(self) -> str:
        return str(self.path)

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}("{self.path}")'