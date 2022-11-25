from pathlib import Path

class YabuException(Exception):
    def __init__(self, msg) -> None:
        super().__init__(msg)
        self.message = msg
    pass

class NotABackupException(YabuException):
    pass

class PresetException(YabuException):
    pass

class BackupException(YabuException):
    def __init__(self, msg, target: Path, destination: Path) -> None:
        self.target = target
        self.destination = destination
        super().__init__(msg)

class PresetNotFoundException(PresetException):
    pass

class InvalidPresetConfig(PresetException):
    pass

class UnsupportedFormatException(BackupException):
    pass

class BackupHashException(BackupException):
    pass

class DestinationNotFoundException(BackupException):
    pass

class TargetNotFoundException(BackupException):
    pass
