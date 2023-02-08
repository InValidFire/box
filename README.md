# YABU

YABU stands for "Yet Another Backup Utility"

## Usage
`yabu list` - list all presets found in the config file.
`yabu backup [-f|-k] <preset>` - create a backup using the `preset`. if the `f` flag is set, force the backup creation even if it was already saved. if the `k` flag is set, keep backups beyond the max_backup_count.
`yabu restore [-d <dir>] <preset>` - restore a backup from the `preset`
`yabu modify <preset>` - modify the `preset`. if the preset does not exist, create a blank one.

YABU loads a file in your HOME directory called `.yabu_config.json`, it should have the following structure:
```json
{
	"format": 1,
	"presets": {
		"minecraft": {
			"targets": [
				"C:\\Users\\Riley\\AppData\\Roaming\\.minecraft\\saves\\survival_world",
				"C:\\Users\\Riley\\AppData\\Roaming\\.minecraft\\saves\\creative_world"
			],
			"destinations": [
				{
					"path": "E:\\backups\\minecraft",
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

## Development

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