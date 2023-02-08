# YABU

YABU stands for "Yet Another Backup Utility"

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

YABU loads a file in your HOME directory called `.yabu_config.json`, it should have the following structure:

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
`yabu list` - list all presets found in the config file.

`yabu backup [-f|-k] <preset>` - create a backup using the `preset`. if the `f` flag is set, force the backup creation even if it was already saved. if the `k` flag is set, keep backups beyond the max_backup_count.

`yabu restore [-d <dir>] <preset>` - restore a backup from the `preset`

`yabu modify <preset>` - modify the `preset`. if the preset does not exist, create a blank one.

## Development and Contribution

To run the program in a development environment, first install the program using pip.

`pip install -e <repo-directory>`

Then you can run the command under the `yabu` command name. :)

---

This program utilizes `pytest` for testing, with `pytest-cov`, ensure you have them both installed:

`pip install pytest pytest-cov`

To run all tests in the tests directory, run the following command in the repo root directory.

`pytest --cov=yabu_cmd ./tests`

If you'd like the report to be generated into an HTML document (for detailed information), run this command instead:

`pytest --cov=yabu_cmd ./tests --cov-report=html`