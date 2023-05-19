from pathlib import Path


class BoxException(Exception):
    def __init__(self, msg) -> None:
        super().__init__(msg)
        self.message = msg

    pass


class NotABackupException(BoxException):
    pass


class PresetException(BoxException):
    pass


class ContentTypeException(BoxException):
    pass


class BackupException(BoxException):
    def __init__(self, msg, target: Path = None, destination: Path = None) -> None:
        self.target = target
        self.destination = destination
        super().__init__(msg)


class DestinationLoopException(BackupException):
    pass


class BackupAbortedException(BackupException):
    pass


class PresetNotFoundException(PresetException):
    pass


class InvalidPresetConfig(PresetException):
    pass


class FormatException(BackupException):
    pass


class BackupHashException(BackupException):
    pass


class DestinationNotFoundException(BackupException):
    pass


class TargetNotFoundException(BackupException):
    pass


class TargetMatchException(BackupException):
    pass
