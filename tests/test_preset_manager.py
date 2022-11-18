from pathlib import Path

import pytest

from yabu_cmd.model.preset_manager import PresetManager
from yabu_cmd.controller.preset import Preset
from yabu_cmd.controller.destination import Destination
from yabu_cmd.exceptions.exceptions import PresetNotFoundException

class TestPresetManager:
    @pytest.fixture
    def new_preset(self):
        preset = Preset("books")
        preset.add_target(Path("cwc"))
        preset.add_destination(Destination(Path("dwd")))
        return preset

    @pytest.fixture
    def preset_json(self):
        import json
        temp_dir = Path("temp")
        temp_dir.mkdir()
        preset_json_file = Path(temp_dir.joinpath("presets.json"))
        preset_json_file.touch()
        presets_data = {
            "format": 1,
            "presets": {
                "minecraft": {
                    "targets": ["awa"],
                    "destinations": [
                        {
                            "path": "bwb",
                            "file_format": "zip",
                            "date_format": "%d_%m_%y__%H%M%S",
                            "max_backup_count": 3,
                            "name_separator": "-"
                        }
                    ]
                }
            }
        }
        preset_json_file.write_text(json.dumps(presets_data, indent=4))
        yield preset_json_file
        preset_json_file.unlink()
        temp_dir.rmdir()

    def test_get_presets(self, preset_json):
        preset_manager = PresetManager(preset_json)
        presets = preset_manager.get_presets()
        assert len(presets) > 0
        for item in presets:
            assert isinstance(item, Preset), "an item is not a Preset"

    def test_pm_getitem(self, preset_json):
        preset_manager = PresetManager(preset_json)
        test_preset = Preset("minecraft")
        test_preset._targets.append(Path("awa"))
        destination = Destination(Path("bwb"))
        test_preset._destinations.append(destination)
        assert preset_manager['minecraft'] == test_preset, ""

    def test_get_preset(self, preset_json):
        preset_manager = PresetManager(preset_json)
        test_preset = Preset("minecraft")
        test_preset._targets.append(Path("awa"))
        destination = Destination(Path("bwb"))
        test_preset._destinations.append(destination)
        preset = preset_manager.get_preset("minecraft")
        assert preset._destinations == test_preset._destinations
        assert preset._targets == test_preset._targets
        assert preset.name == test_preset.name
        assert preset_manager.get_preset("minecraft") == test_preset

    def test_get_nonexistant_preset(self, preset_json):
        preset_manager = PresetManager(preset_json)
        with pytest.raises(PresetNotFoundException):
            preset_manager.get_preset("books")

    def test_save_preset_correct(self, preset_json, new_preset):
        preset_manager = PresetManager(preset_json)
        preset = Preset("books")
        preset.add_target(Path("cwc"))
        preset.add_destination(Destination(Path("dwd")))
        preset_manager.save_preset(preset)
        # try to get saved preset back
        assert preset_manager['books'] == new_preset

    def test_save_preset_incorrect_destination(self, preset_json):
        preset_manager = PresetManager(preset_json)
        preset = Preset("books")
        preset.add_target(Path("cwc"))
        with pytest.raises(TypeError):
            preset.add_destination(Destination("dwd"))
        preset_manager.save_preset(preset)

    def test_save_preset_incorrect(self, preset_json):
        preset_manager = PresetManager(preset_json)
        preset = Preset("books")
        with pytest.raises(TypeError):
            preset.add_target("cwc")
            preset.add_destination("dwd")
        preset_manager.save_preset(preset)

    def test_delete_preset(self, preset_json):
        preset_manager = PresetManager(preset_json)
        preset = preset_manager.get_preset("minecraft")
        preset_manager.delete_preset(preset)
        assert len(preset_manager.get_presets()) == 0

    def test_delete_nonexistant_preset(self, preset_json):
        preset_manager = PresetManager(preset_json)
        preset = Preset("books")
        preset._targets.append(Path("cwc"))
        preset._destinations.append(Destination(Path("dwd")))
        with pytest.raises(PresetNotFoundException):
            preset_manager.delete_preset(preset)