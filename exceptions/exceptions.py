from pathlib import Path

class BackupException(Exception):
    pass

class PresetNotFoundException(BackupException):
    pass

class InvalidPresetConfig(BackupException):
    def __init__(self, msg) -> None:
        super().__init__(msg)
        self.message = msg
    pass