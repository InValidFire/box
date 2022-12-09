from pathlib import Path

from yabu_cmd.controller import CommandHandler
from yabu_cmd.exceptions import (
    PresetNotFoundException,
    TargetNotFoundException,
    DestinationNotFoundException,
    BackupHashException,
    FormatException,
    ContentTypeException,
    TargetMatchException,
)

import click


@click.group()
@click.option("--config", "-c", default=Path.home().joinpath(".yabu_presets.json"))
@click.pass_context
def cli(ctx: click.Context, config):
    ctx.ensure_object(dict)
    ctx.obj["config"] = config
    pass


@cli.command()
@click.pass_obj
def presets(obj):
    """List all presets found in the preset config.

    Args:
        obj (dict): Click's context object.
    """
    handler = CommandHandler(obj["config"])
    try:
        for preset in handler.list_presets():
            print(preset)
    except FileNotFoundError:
        print(f"Uh-Oh! Your config file appears to be missing: '{obj['config']}'")
    except ValueError:
        print(
            f"The path exists, it doesn't seem to be a .json file though: '{obj['config']}'"
        )


@cli.command()
@click.option("--force", "-f", default=False)
@click.option("--keep", "-k", default=False)
@click.argument("preset")
@click.pass_obj
def backup(obj, preset: str, force: bool, keep: bool):
    """Create a backup of a preset's targets.

    Args:
        obj (dict): Click's context object.
        preset (str): The preset name to create backups for.
        force (bool): Whether or not to force backup creation, even if an
            identical backup exists.
        keep (bool): Whether or not to keep backups beyond the
            max_backup_count.

    Raises:
        backup: If a problem is found in the backup generator, the exceptions
            will be raised here.
    """
    print("Creating backups...")
    handler = CommandHandler(obj["config"])
    print("Please wait for backups to be created: ")
    for backup in handler.create_backups(preset, force, keep):
        try:
            if isinstance(backup, Exception):
                raise backup  # backup generator might yield exceptions since it can't raise them personally.
        except PresetNotFoundException:
            print(f"The requested preset '{obj['location']}' is not found.")
        except TargetNotFoundException as e:
            print(
                f"Backup Failed:\n\tTarget not found:\n\tTarget: {e.target}\n\tDestination: {e.destination}"
            )
        except DestinationNotFoundException as e:
            print(
                f"Backup Failed:\n\Destination not found:\n\tTarget: {e.target}\n\tDestination: {e.destination}"
            )
        except BackupHashException as e:
            print(
                f"Backup Failed:\n\tBackup hash matched latest backup in destination path.\n\tTarget: {e.target}\n\tDestination: {e.destination}"
            )
        except FormatException as e:
            print(
                f"Backup Failed:\n\tBackup format unsupported\n\tTarget: {e.target}\n\Destination: {e.destination}"
            )
        else:
            print(backup)


@cli.command()
@click.option("--dir", "-d", type=bool, default=False, is_flag=True)
@click.argument("location")
@click.pass_obj
def restore(obj, location: str, path: bool):
    """Restore a backup to its target.

    Args:
        obj (dict): Click's context object.
        location (str): The location where backups are stored, can either be a
            preset name, or a directory path. If it is a preset, it loads all
            backups from the destinations in the preset.
        path (bool): Whether or not we are loading backups from a directory
            path.

    Usage:
        `yabu restore <preset>`
        `yabu restore -d <path>`
        `yabu restore <path> -d`
    """
    handler = CommandHandler(obj["config"])
    try:
        if path:
            location = Path(location)
    except PresetNotFoundException:
        print(f"The requested preset '{obj['location']}' is not found.")

    backups = handler.list_backups(location)
    selected_backup = None
    while selected_backup == None:
        try:
            print("\nBackups:")
            for i, backup in enumerate(backups, start=1):
                print(f"{i}. {backup.name} - {backup.date}")
            selected_backup = int(input("\nSelect a backup to restore: "))
            selected_backup = backups[selected_backup - 1]
        except ValueError:
            print("The value entered is not a number...")
            continue
        except IndexError:
            print("There is no backup matching the entered value...")
            selected_backup = None
            continue
    try:
        print(f"restoring {selected_backup.path} to {selected_backup.target}")
        handler.restore_backup(location=selected_backup.target, backup=selected_backup)
    except FileNotFoundError:
        print("The parent path of the target does not exist. Aborting restore.")
    except ContentTypeException:
        print(
            f"The content type of the backup does not match the target path. You're trying to restore a {selected_backup.content_type} backup while targeting something else."
        )
    except FormatException:
        print("The backup is stored in an unsupported format.")
    except TargetMatchException:
        print(
            "The backup's target does not match the preset target."
        )  # currently I don't think there's a way to reach this message.


if __name__ == "__main__":
    cli()
