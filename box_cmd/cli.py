import os

from pathlib import Path

from . import CommandHandler, ProgressInfo, Backup
from .exceptions import (
    PresetNotFoundException,
    TargetNotFoundException,
    DestinationNotFoundException,
    BackupHashException,
    FormatException,
    ContentTypeException,
    TargetMatchException,
    BackupAbortedException,
    DestinationLoopException
)

import click
from tqdm import tqdm

__version__ = "2.0.2"

@click.group()
@click.version_option(__version__)
@click.option("--config", "-c", default=Path.home().joinpath(".box_presets.json"))
@click.pass_context
def cli(ctx: click.Context, config):
    ctx.ensure_object(dict)
    ctx.obj["config"] = config
    pass


@cli.command(help="List all presets found in the preset config.")
@click.pass_obj
def presets(obj):
    """List all presets found in the preset config.

    Args:
        obj (dict): Click's context object.
    """
    try:
        handler = CommandHandler(obj["config"])
        print(f"Loading presets from {obj['config']}\n\nPresets:")
        for preset in handler.list_presets():
            try:
                print("-" * os.get_terminal_size().columns)
            except OSError:
                print("-" * 10)
            print(preset)
    except FileNotFoundError:
        print(f"Uh-Oh! Your config file appears to be missing: '{obj['config']}'")
    except ValueError:
        print(
            f"The path exists, it doesn't seem to be a .json file though: '{obj['config']}'"
        )
    except IsADirectoryError:
        print(
            f"The path exists, but this looks like a directory. Please ensure the path is correct: {obj['config']}"
        )

@cli.command(help="Create a backup of a preset.")
@click.option("--force", "-f", default=False, help="Force the creation of a backup, even if a duplicate already exists.")
@click.option("--keep", "-k", default=False, help="Keep the backup even if it surpasses the preset's max_backup_count.")
@click.argument("preset")
@click.pass_obj
def pack(obj, preset: str, force: bool, keep: bool):
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

    Usage:
        `box pack <preset> [--force] [--keep]`
    """
    print("Creating backups...")
    handler = CommandHandler(obj["config"])
    items: list[Backup, Exception] = []
    progress_bar = tqdm()
    for item in handler.create_backups(preset, force, keep):
        if isinstance(item, ProgressInfo):  # handle progress bar stuff
            progress_bar.update(item.count)
            if item.total is not None:
                progress_bar.reset(total=item.total)
            if item.msg is not None:
                progress_bar.set_description(f"{item.msg}")
        else:
            items.append(item)
    progress_bar.close()

    for item in items:
        try:
            if isinstance(item, Exception):
                raise item  # backup generator might yield exceptions since it can't raise them personally.
            elif isinstance(item, Backup):
                print(item)
            else:
                raise TypeError(item)
        except PresetNotFoundException:
            print(f"The requested preset '{obj['location']}' is not found.")
        except TargetNotFoundException as e:
            print(
                f"Backup Failed:\n\tTarget not found:\n\tTarget: {e.target}\n\tDestination: {e.destination}"
            )
        except DestinationNotFoundException as e:
            print(
                f"Backup Failed:\n\tDestination not found:\n\tTarget: {e.target}\n\tDestination: {e.destination}"
            )
        except BackupHashException as e:
            print(
                f"Backup Skipped:\n\tBackup hash matched latest backup in destination path.\n\tTarget: {e.target}\n\tDestination: {e.destination}"
            )
        except FormatException as e:
            print(
                f"Backup Failed:\n\tBackup format unsupported\n\tTarget: {e.target}\n\tDestination: {e.destination}"
            )
        except BackupAbortedException as e:
            print(
                f"Backup Aborted:\n\tTarget: {e.target}\n\tDestination: {e.destination}"
            )
        except DestinationLoopException as e:
            print(
                f"The destination: {e.destination} is contained within the target: {e.target}. Aborting..."
            )


@cli.command(help="Restore a backup to its target or a custom destination.")
@click.option("--source", required=True, help="The backup source, either a preset name, or a folder where backups are stored.")
@click.option("--destination", required=False, help="The destination to restore to. Not required, backups will try to restore to their original location by default.")
@click.pass_obj
def unpack(obj, source: str, destination: str = None):
    """Restore a backup to its target or a custom destination.

    Args:
        obj (dict): Click's context object.
        source (str): The location where backups are stored, can either be a
            preset name, or a directory path. If it is a preset, it loads all
            backups from the destinations in the preset, and gives you the opportunity to select one.
        destination (bool) [Optional]: The destination path to restore to.

    Usage:
        `box unpack --source <source> [--destination destination]`
    """
    handler = CommandHandler(obj["config"])
    if source not in handler.list_presets() and Path(source).exists():
        source = Path(source)

    try:
        backups = handler.list_backups(source)
    except FileNotFoundError:
        print("Source path doesn't exist. :(")
        return
    except PresetNotFoundException:
        print("The requested preset is not found. :(")
        return

    selected_backup = None
    while selected_backup is None:
        try:
            print("\nBackups:")
            for i, backup in enumerate(backups, start=1):
                print(f"{i}. {backup.name} - {backup.date}")
            selected_backup = int(
                input("\nSelect a backup to restore (CTRL-C to cancel): ")
            )
            selected_backup = backups[selected_backup - 1]
        except ValueError:
            print("The value entered is not a number...")
            continue
        except IndexError:
            print("There is no backup matching the entered value...")
            selected_backup = None
            continue
        if destination is None:
            restore_location = selected_backup.target
        else:
            restore_location = destination
        print(f"The following backup will be restored:\n{selected_backup}\n")
        if destination is None:
            print(f"Restore destination: {restore_location}")
        confirm = input("Continue? (y/n): ")
        if confirm.lower() != "y":
            selected_backup = None
    try:
        print(f"restoring {selected_backup.path} to {restore_location}")
        handler.restore_backup(location=restore_location, backup=selected_backup)
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
