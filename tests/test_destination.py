import json

from yabu_cmd import Destination


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
