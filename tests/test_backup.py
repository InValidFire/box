from yabu_cmd import PresetManager, BackupManager


class TestBackup:
    def test_backup_str(self, preset_json):
        preset_manager = PresetManager(preset_json)
        presets = preset_manager.get_presets()
        backup_manager = BackupManager()
        backup_manager.create_backups(presets[0])
        for backup in backup_manager.get_backups(presets[0]):
            backup_str = str(backup)
            print(repr(backup_str))
            correct_output = f"""Backup:
\tname: folder
\tpath: C:\\Users\\Riley\\.storage\\programs\\backup_cmd\\temp\\{backup.name}{backup.name_separator}{backup.date.strftime(backup.date_format)}.zip
\tdate_format: %d_%m_%y__%H%M%S%f
\tname_separator: -
\ttarget: C:\\Users\\Riley\\.storage\\programs\\backup_cmd\\temp\\folder
\tdate: {backup.date}
\tcontent_hash: {backup.content_hash}"""
            assert backup_str == correct_output
