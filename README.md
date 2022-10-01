# backup_cmd
A command-line tool to easily create backups of selected folders.

# Setup

In order to use this, you need to make a folder in your home directory labeled ".storage".

Inside the .storage folder, you'll have a file named ".backup_data.json" where you'll specify what to backup and where to store it.

Here's an example of my current .backup_data.json:
```json
{
    "minecraft": {
        "targets": [
            "C:\\Users\\InValidFire\\AppData\\Roaming\\.minecraft\\saves\\main_world",
            "C:\\Users\\InValidFire\\AppData\\Roaming\\.minecraft\\saves\\building_world"
        ],
        "destinations": [
            {
                "path": "C:\\Users\\InValidFire\\.storage\\backups",
                "max_count": 3
            },
            {
                "path": "D:\\backups",
                "max_count": 10
            }
        ]
    }
}
```
preset:
    targets (list) - the target directories to backup

    destinations (list)
        path (str) - the destination to copy the target(s) to.
        max_count (int) - the maximum count of backups to store. (oldest gets deleted after this many backups are made)

# Usage

## Backup

Simply run main.py with the preset of which backup to run. For example:

`python main.py minecraft`

Running this command will add every file found in the target directory to a zip, and place that zip in each of the destinations.

## Restore

If you wish to restore a backup add a `-r` or `--restore` flag:

`python main.py minecraft -r`

It will list the choices in all accessible backup locations for you to choose from, and restore your chosen backup.

This can of course be aliased.