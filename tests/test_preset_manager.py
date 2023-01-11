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
        preset.add_target(Path("tempFolder"))
        preset.add_destination(Destination(Path("temp")))
        return preset

    def test_get_presets(self, preset_json):
        preset_manager = PresetManager(preset_json)
        presets = preset_manager.get_presets()
        assert len(presets) > 0
        for item in presets:
            assert isinstance(item, Preset), "an item is not a Preset"

    def test_pm_getitem(self, preset_json):
        preset_manager = PresetManager(preset_json)
        test_preset = Preset("testFolder")
        test_preset._targets.append(Path("temp/folder").absolute())
        destination = Destination(Path("temp").absolute())
        test_preset._destinations.append(destination)
        assert preset_manager["testFolder"] == test_preset

    def test_get_preset(self, preset_json):
        preset_manager = PresetManager(preset_json)
        test_preset = Preset("testFolder")
        test_preset._targets.append(Path("temp/folder").absolute())
        destination = Destination(Path("temp").absolute())
        test_preset._destinations.append(destination)
        assert preset_manager.get_preset("testFolder") == test_preset

    def test_get_nonexistant_preset(self, preset_json):
        preset_manager = PresetManager(preset_json)
        with pytest.raises(PresetNotFoundException):
            preset_manager.get_preset("books")

    def test_save_preset_correct(self, preset_json):
        preset_manager = PresetManager(preset_json)
        preset = Preset("books")
        preset.add_target(Path("temp/folder"))
        preset.add_destination(Destination(Path("temp")))
        preset_manager.save_preset(preset)
        # try to get saved preset back
        assert preset_manager["books"] == preset

    def test_save_preset_incorrect_destination(self, preset_json):
        preset_manager = PresetManager(preset_json)
        preset = Preset("books")
        preset.add_target(Path("temp/folder"))
        with pytest.raises(TypeError):
            preset.add_destination(Destination("temp"))
        preset_manager.save_preset(preset)

    def test_save_preset_incorrect(self, preset_json):
        preset_manager = PresetManager(preset_json)
        preset = Preset("books")
        with pytest.raises(TypeError):
            preset.add_target("temp/folder")
            preset.add_destination("temp")
        preset_manager.save_preset(preset)

    def test_delete_preset(self, preset_json):
        preset_manager = PresetManager(preset_json)
        preset = preset_manager.get_preset("testFile")
        preset_manager.delete_preset(preset)
        assert len(preset_manager.get_presets()) == 1

    def test_delete_nonexistant_preset(self, preset_json):
        preset_manager = PresetManager(preset_json)
        preset = Preset("books")
        preset.add_target(Path("temp/folder"))
        preset.add_destination(Destination(Path("temp")))
        with pytest.raises(PresetNotFoundException):
            preset_manager.delete_preset(preset)
