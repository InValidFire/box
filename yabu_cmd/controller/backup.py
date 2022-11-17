from dataclasses import dataclass
from pathlib import Path

__all__ = ['Backup']

@dataclass(frozen=True)
class Backup:
    name: str = None
    path: Path = None
    date_format: str = None
    separator: str = None
    target: Path = None