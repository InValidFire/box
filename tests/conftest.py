from pathlib import Path
import shutil

import pytest


@pytest.fixture
def preset_json():
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
                        "path": str(temp_dir.absolute()),
                        "file_format": "zip",
                        "date_format": "%Y_%m_%d__%H%M%S",
                        "max_backup_count": 3,
                        "name_separator": "-",
                    }
                ],
            },
            "testFile": {
                "targets": [str(file.absolute())],
                "destinations": [
                    {
                        "path": str(temp_dir.absolute()),
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
