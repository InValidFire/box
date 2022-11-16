from dataclasses import dataclass

__all__ = ['Backup']

@dataclass(frozen=True)
class Backup:
    name: str = None
    date_format: str = None
    separator: str = None