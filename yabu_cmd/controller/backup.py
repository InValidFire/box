from dataclasses import dataclass
from pathlib import Path
from datetime import datetime

__all__ = ["Backup"]


@dataclass(frozen=True, repr=True)
class Backup:
    name: str = None
    path: Path = None
    date_format: str = None
    name_separator: str = None
    target: Path = None
    date: datetime = None
    content_hash: str = None
    content_type: str = None

    def __str__(self) -> str:
        output = "Backup:"
        output += f"\n\tname: {self.name}"
        output += f"\n\ttarget: {self.target}"
        output += f"\n\tpath: {self.path}"
        output += f"\n\tdate: {self.date}"
        return output
