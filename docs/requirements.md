## Requirements

### System
0. create and manage backup presets and backups using a terminal UI.
1. allow for backups to be restored through the terminal UI.

### Backup Presets
0. backup creation and restoration is to be triggered through backup presets.
1. backup presets are to be saved in a human-readable format.
2. backup presets should have a unique name to serve as the preset identifier.
3. backup presets will store the paths of target directories & files, as well as the paths of destination directories.
	1. each backup target will have a backup created and stored in each destination, allowing for backups to multiple locations.
4. keep a backlog of past backups, the amount customizable to each destination.
5. backup presets will allow the user to select a supported file format for the backup, customizable to each destination.

### Backups
0. backups are to be stored in universal compressed formats, such as .zip, 7z, or .tar.
1. backup file names are to have the name of the file or folder, along with the backup creation date.
2. backups should know what their name, date format, and separator is, in the event the preset is changed.

### Restoring
0. user will be shown all unique backups found on the file system.
1. user can pick a backup to restore.
2. user can choose to delete a backup upon restoration.