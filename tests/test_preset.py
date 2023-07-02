from pathlib import Path
import shutil
import json

import pytest

from box_cmd.preset import Preset
from box_cmd.destination import Destination
from box_cmd.backup import Backup
from box_cmd.exceptions.exceptions import PresetNotFoundException, BackupHashException, BoxException, DestinationLoopException
from box_cmd.progress_info import ProgressInfo


class TestPreset:
    def test_get_presets(self, preset_json):
        Preset.load_file(preset_json)
        presets = Preset.get_presets()
        assert len(presets) > 0
        for item in presets:
            assert isinstance(item, Preset), "an item is not a Preset"

    def test_get_preset(self, preset_json):
        Preset.load_file(preset_json)
        test_preset = Preset("testFolder")
        test_preset._targets.append(Path("temp/folder").absolute())
        destination = Destination(Path("temp").absolute())
        test_preset._destinations.append(destination)
        assert Preset.get_preset("testFolder") == test_preset

    def test_get_nonexistant_preset(self, preset_json):
        Preset.load_file(preset_json)
        with pytest.raises(PresetNotFoundException):
            Preset.get_preset("books")

    def test_save_preset_correct(self, preset_json):
        Preset.load_file(preset_json)
        preset = Preset("books")
        preset.add_target(Path("temp/folder"))
        preset.add_destination(Destination(Path("temp")))
        preset.save()
        # try to get saved preset back
        assert Preset.get_preset("books") == preset

    def test_save_preset_incorrect_destination(self, preset_json):
        Preset.load_file(preset_json)
        preset = Preset("books")
        preset.add_target(Path("temp/folder"))
        with pytest.raises(TypeError):
            preset.add_destination(Destination("temp"))
        preset.save()

    def test_save_preset_incorrect(self, preset_json):
        Preset.load_file(preset_json)
        preset = Preset("books")
        with pytest.raises(TypeError):
            preset.add_target("temp/folder")
            preset.add_destination("temp")
        preset.save()

    def test_delete_preset(self, preset_json):
        Preset.load_file(preset_json)
        preset = Preset.get_preset("testFile")
        preset.delete()
        assert len(Preset.get_presets()) == 1

    def test_delete_nonexistant_preset(self, preset_json):
        Preset.load_file(preset_json)
        preset = Preset("books")
        preset.add_target(Path("temp/folder"))
        preset.add_destination(Destination(Path("temp")))
        with pytest.raises(PresetNotFoundException):
            preset.delete()

    @pytest.fixture
    def destination_loop(self):
        import json

        temp_dir = Path("temp")
        folder = temp_dir.joinpath("folder")
        sub_folder = folder.joinpath("sub_folder")
        file = sub_folder.joinpath("file.txt")
        sub_folder.mkdir(parents=True)
        file.touch()  # set up rudamentary test environment
        file.write_text("This is a test file. :)")  # :)
        preset_json_file = Path(temp_dir.joinpath("presets.json"))
        preset_json_file.touch()
        presets_data = {
            "format": 1,
            "presets": {
                "testFolder": {
                    "targets": [str(folder.absolute())],
                    "destinations": [
                        {
                            "path": str(sub_folder.absolute()),
                            "file_format": "zip",
                            "date_format": "%Y_%m_%d__%H%M%S",
                            "max_backup_count": 3,
                            "name_separator": "-",
                        }
                    ],
                },
            },
        }
        preset_json_file.write_text(json.dumps(presets_data, indent=4))
        yield preset_json_file
        shutil.rmtree(temp_dir)

    def test_create_backups_destination_loop(self, destination_loop):
        Preset.load_file(destination_loop)
        presets = Preset.get_presets()
        for preset in presets:
            with pytest.raises(DestinationLoopException):
                for exception in preset.create_backups():
                    if not isinstance(exception, BoxException):
                        continue
                    raise exception

    def test_create_backups_zip_no_force_no_keep(self, preset_json):
        Preset.load_file(preset_json)
        presets = Preset.get_presets()
        for preset in presets:
            print(preset)
            for backup in preset.create_backups(False, False):
                if isinstance(backup, ProgressInfo):
                    continue
                assert isinstance(backup, Backup)
                if preset.name == "testFile":
                    assert backup.name == "file"
                    assert backup.date_format == "%Y_%m_%d__%H%M%S"
                    assert backup.name_separator == "-"
                    assert str(backup.target) == str(
                        Path("temp/folder/sub_folder/file.txt").absolute()
                    )  # allows Path and its children to equate. :)
                if preset.name == "testFolder":
                    assert backup.name == "folder"
                    assert backup.date_format == "%Y_%m_%d__%H%M%S"
                    assert backup.name_separator == "-"
                    assert str(backup.target) == str(
                        Path("temp/folder").absolute()
                    )  # allows Path and its children to equate. :)

    def test_create_backups_zip_force_no_keep(self, preset_json):
        Preset.load_file(preset_json)
        presets = Preset.get_presets()
        for i in range(4):
            for preset in presets:
                for destination in preset._destinations:
                    destination.date_format = "%Y_%m_%d__%H%M%S%f"  # these need to include the microseconds due to the rate at which backups are created.
                for backup in preset.create_backups(True, False):
                    if isinstance(backup, ProgressInfo):
                        continue
                    assert isinstance(backup, Backup)
        testFile_count = 0
        testFolder_count = 0
        for file in Path("temp").glob("file*.zip"):
            testFile_count += 1
        for file in Path("temp").glob("folder*.zip"):
            testFolder_count += 1
        assert testFile_count == 3
        assert testFolder_count == 3

    def test_create_backups_zip_force_keep(self, preset_json):
        Preset.load_file(preset_json)
        presets = Preset.get_presets()
        for i in range(4):
            print(i)
            for preset in presets:
                for destination in preset._destinations:
                    destination.date_format = "%Y_%m_%d__%H%M%S%f"  # these need to include the microseconds due to the rate at which backups are created.
                for backup in preset.create_backups(True, True):
                    if isinstance(backup, ProgressInfo):
                        continue
                    assert isinstance(backup, Backup)
        testFile_count = 0
        testFolder_count = 0
        for file in Path("temp").glob("file*.zip"):
            testFile_count += 1
        for file in Path("temp").glob("folder*.zip"):
            testFolder_count += 1
        assert testFile_count == 4
        assert testFolder_count == 4

    def test_create_backup_already_exists(self, preset_json):
        Preset.load_file(preset_json)
        presets = Preset.get_presets()
        for preset in presets:
            for _ in preset.create_backups():
                continue
            with pytest.raises(BackupHashException):
                for exception in preset.create_backups():
                    if isinstance(exception, BoxException):
                        raise exception

    def test_metafile_generation(self, preset_json):
        Preset.load_file(preset_json)
        preset = Preset.get_preset("testFolder")
        target = preset._targets[0]
        destination = preset._destinations[0]
        md5_hash = None
        for i in preset.create_md5_hash(target):
            if isinstance(i, ProgressInfo):
                continue
            if isinstance(i, str):
                md5_hash = i
        metafile_str = preset._create_metafile(target, destination, md5_hash)

        metafile_json = json.loads(metafile_str)

        assert len(metafile_json.keys()) == 5
        assert metafile_json['target'] == str(target)
        assert metafile_json['name_separator'] == destination.name_separator
        assert metafile_json['date_format'] == destination.date_format
        assert metafile_json['content_hash'] == md5_hash
        assert metafile_json['content_type'] == "folder"

    def test_restore_backup(self, preset_json):
        Preset.load_file(preset_json)

        for preset in Preset.get_presets():
            for backup in preset.create_backups():
                if isinstance(backup, Backup):
                    if backup.target.is_dir():
                        shutil.rmtree(backup.target)
                    elif backup.target.is_file():
                        backup.target.unlink()

                    assert not backup.target.exists()

                    backup.restore()

                    assert backup.target.exists()

    def test_restore_backup_overwrite_directory(self, preset_json):
        Preset.load_file(preset_json)
        for preset in Preset.get_presets():
            if preset.name != "testFolder":
                continue
            for backup in preset.create_backups():
                if not isinstance(backup, Backup):
                    continue
                temp_file = preset._targets[0].joinpath("temp")
                backup.restore()
                assert not temp_file.exists()
