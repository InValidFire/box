import json
from pathlib import Path

from box_cmd import Destination, Preset


class TestDestination:
    def test_from_json(self, preset_json):
        with preset_json.open("r") as f:
            preset_json = json.load(f)

        for i, destination in enumerate(preset_json['presets']['testFolder']['destinations']):
            destination = Destination.from_dict(destination)

            destination_json = preset_json['presets']['testFolder']['destinations'][i]

            assert destination.file_format == destination_json['file_format']
            assert destination.name_separator == destination_json['name_separator']
            assert destination.max_backup_count == destination_json['max_backup_count']
            assert destination.date_format == destination_json['date_format']
            assert str(destination.path) == destination_json['path']

    def test_get_backups(self, preset_json):
        Preset.load_file(preset_json)
        for preset in Preset.get_presets():
            for _ in preset.create_backups(preset):
                pass

            for destination in preset._destinations:
                backups = destination.get_backups()

                file_count = 0
                for _ in Path(destination.path).glob(f"*.{destination.file_format}"):
                    file_count += 1

                assert len(backups) == file_count  # ensures it finds all created backups in the Destination

                for target in preset._targets:
                    for backup in destination.get_backups(target):
                        assert backup.target == target
