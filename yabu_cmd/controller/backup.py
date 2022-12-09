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
        output += f"\n\tpath: {self.path}"
        output += f"\n\tdate_format: {self.date_format}"
        output += f"\n\tname_separator: {self.name_separator}"
        output += f"\n\ttarget: {self.target}"
        output += f"\n\tdate: {self.date}"
        output += f"\n\tcontent_hash: {self.content_hash}"
        output += f"\n\tcontent_type: {self.content_type}"
        return output
