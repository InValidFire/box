from pathlib import Path

from ..controller.destination import Destination

__all__ = ['DestinationManager']

class DestinationManager:
    def get_destination(self, destination_dict: dict):
        destination = Destination(path=Path(destination_dict['path']))
        if "date_format" in destination_dict:
            destination.date_format = destination_dict['date_format']
        if "name_separator" in destination_dict:
            destination.name_separator = destination_dict['name_separator']
        if "max_backup_count" in destination_dict:
            destination.max_backup_count = destination_dict['max_backup_count']
        if "file_format" in destination_dict:
            destination.file_format = destination_dict['file_format']
        return destination