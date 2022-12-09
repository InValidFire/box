from pathlib import Path

from click.testing import CliRunner
import pytest

from yabu_cmd.cli import cli


class TestCLI:
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
                            "name_separator": "-",
                        }
                    ],
                }
            },
        }
        preset_json_file.write_text(json.dumps(presets_data, indent=4))
        yield preset_json_file
        preset_json_file.unlink()
        temp_dir.rmdir()

    def test_presets_cmd(self, preset_json):
        runner = CliRunner()
        result = runner.invoke(cli, "--config temp/presets.json presets".split())
        assert "minecraft" in result.output
        assert "Targets:" in result.output
        assert "- awa" in result.output
        assert "Destinations:" in result.output
        assert "- bwb" in result.output
        assert "File Format:" in result.output
        assert "Max Backup Count:" in result.output
        assert "Date Format:" in result.output
        assert "Name Separator:" in result.output

    def test_presets_cmd_not_found(self):
        runner = CliRunner()
        result = runner.invoke(cli, "--config temp/presets.json presets".split())
        assert "Uh-Oh! Your config file appears to be missing:" in result.output

    def test_presets_cmd_not_file(self, preset_json):
        runner = CliRunner()
        result = runner.invoke(cli, "--config temp presets".split())
        assert (
            "The path exists, it doesn't seem to be a .json file though:"
            in result.output
        )
