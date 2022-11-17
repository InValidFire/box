from pathlib import Path

class BackupException(Exception):
    def __init__(self, msg) -> None:
        super().__init__(msg)
        self.message = msg
    pass

class PresetNotFoundException(BackupException):
    pass

class InvalidPresetConfig(BackupException):
    pass

class UnsupportedFormatException(BackupException):
    pass

class NotABackupException(BackupException):
    pass