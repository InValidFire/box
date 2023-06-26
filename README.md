# BOX

Box is a command line tool that enables the easy creation of rolling backups using user-defined presets.

## Installation

### Pre-Installation

Ensure you have the following tools configured and working on your machine.
- Python (3.7 or greater)
- Git

Follow these steps to install this utility.

1. Clone the repository using git:
	- `git clone https://github.com/InValidFire/backup_cmd.git` (https)
	- `git clone git@github.com:InValidFire/backup_cmd.git` (ssh)
2. Navigate into the root of the repository.
3. Use pip to install the package locally.
	- `python -m pip install .`

> Note: Depending on your system's configuration, the exact commands to run may vary.

### Post-Installation and Configuration

BOX loads a file in your HOME directory called `.box_config.json`, it should have the following structure:

```json
{
	"format": 1,
	"presets": {
		"<preset_name>": {
			"targets": [
				"C:\\Target\\Path\\One",
				"C:\\Target\\Path\\Two"
			],
			"destinations": [
				{
					"path": "E:\\Destination\\Path",
					"file_format": "zip",
					"name_separator": "-",
					"date_format": "%d_%m_%y__%H%M%S",
					"max_backup_count": 10
				}
			]
		}
	}
}
```

> If you'd like to see the JSON Schema used to validate this file, see here: [presets.json JSON Schema](docs/presets_schema.json)

---

## Usage
`box list` - list all presets found in the config file.

`box pack [--force] [--keep] <preset>` - create a backup using the `preset`. if the `force` flag is set, force the backup creation even if it was already saved. if the `keep` flag is set, keep backups beyond the max_backup_count.

`box unpack --source=<preset|backups_folder> [--destination <destination_path>]` - select a backup to restore from the `preset` or `backups_folder` path. The `backups_folder` path should contain completed backups from the utility. If the `destination` is given, the original backup's target will not be used and the backup will instead be restored to the custom destination.

## Development and Contribution

To run the program in a development environment, first install the program using pip.

`pip install -e <repo-directory>`

Then you can run the command under the `box` command name. :)

---

This program utilizes `pytest` for testing, with `pytest-cov`, ensure you have them both installed:

`pip install pytest pytest-cov`

To run all tests in the tests directory, run the following command in the repo root directory.

`pytest --cov=box_cmd ./tests`

If you'd like the report to be generated into an HTML document (for detailed information), run this command instead:

`pytest --cov=box_cmd ./tests --cov-report=html`