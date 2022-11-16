from pathlib import Path

from ..model.preset_manager import PresetManager
from ..controller.preset import Preset
from ..controller.destination import Destination

class TestPresetManager:
    def test_get_presets(self):
        preset_manager = PresetManager("presets.json")
        presets = preset_manager.get_presets()
        assert len(presets) > 0
        for item in presets:
            assert isinstance(item, Preset)

    def test_pm_getitem(self):
        preset_manager = PresetManager("presets.json")
        test_preset = Preset("minecraft")
        test_preset.targets.append(Path("awa"))
        destination = Destination(Path("bwb"))
        test_preset.destinations.append(destination)
        assert preset_manager['minecraft'] == test_preset

    def test_pm_get_preset(self):
        preset_manager = PresetManager("presets.json")
        test_preset = Preset("minecraft")
        test_preset.targets.append(Path("awa"))
        destination = Destination(Path("bwb"))
        test_preset.destinations.append(destination)
        preset = preset_manager.get_preset("minecraft")
        assert preset.destinations == test_preset.destinations
        assert preset.targets == test_preset.targets
        assert preset.name == test_preset.name
        assert preset_manager.get_preset("minecraft") == test_preset

    def test_delete_preset(self):
        preset_manager = PresetManager("presets.json")
        preset = preset_manager.get_preset("minecraft")
        preset_manager.delete_preset(preset)
        assert len(preset_manager.get_presets()) == 0