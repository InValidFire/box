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
            "C:\\Users\\InValidFire\\.storage\\backups"
        ],
        "max_count": 3
    }
}
```

targets - the target directories to backup

destinations - the destinations to copy the target(s) to.

max_count - the maximum count of backups to store. (oldest gets deleted after this many backups are made)

# Usage

Simply run main.py with the key of which backup to run. For example:

`python main.py minecraft`

This can of course be aliased.