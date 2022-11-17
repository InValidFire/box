from dataclasses import dataclass
from pathlib import Path
from datetime import datetime

__all__ = ['Backup']

@dataclass(frozen=True)
class Backup:
    name: str = None
    path: Path = None
    date_format: str = None
    separator: str = None
    target: Path = None
    date: datetime = None
    md5_hash: str = None