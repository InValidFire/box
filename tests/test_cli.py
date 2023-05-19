from pathlib import Path

from click.testing import CliRunner

from box_cmd.cli import cli


class TestCLI:
    def test_presets_cmd(self, preset_json):
        runner = CliRunner()
        result = runner.invoke(cli, "--config temp/presets.json presets".split())
        assert "testFolder" in result.output
        assert "Targets:" in result.output
        assert f"- {Path('temp/folder').absolute()}" in result.output
        assert "Destinations:" in result.output
        assert f"- {Path('temp').absolute()}" in result.output
        assert "File Format:" in result.output
        assert "Max Backup Count:" in result.output
        assert "Date Format:" in result.output
        assert "Name Separator:" in result.output

    def test_presets_cmd_not_found(self):
        runner = CliRunner()
        result = runner.invoke(cli, "--config temp/presets.json presets".split())
        assert "Uh-Oh! Your config file appears to be missing:" in result.output

    def test_presets_cmd_not_file_is_folder(self, preset_json):
        runner = CliRunner()
        result = runner.invoke(cli, "--config temp presets".split())
        assert (
            "The path exists, but this looks like a directory. Please ensure the path is correct:"
            in result.output
        )

    def test_presets_cmd_not_file(self, preset_json):
        runner = CliRunner()
        result = runner.invoke(cli, "--config temp/folder/sub_folder/file.txt presets")
        assert "The path exists, it doesn't seem to be a .json file though:" in result.output
