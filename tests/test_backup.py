from box_cmd import Preset


class TestBackup:
    def test_backup_str(self, preset_json):
        Preset.load_file(preset_json)
        presets = Preset.get_presets()
        presets[0].create_backups()
        for backup in presets[0].get_backups():
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
