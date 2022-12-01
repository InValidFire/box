from pathlib import Path
import click

from yabu_cmd.controller import CommandHandler
from yabu_cmd.controller import Destination
from yabu_cmd.exceptions import PresetNotFoundException, TargetNotFoundException, DestinationNotFoundException, BackupHashException, FormatException

@click.group()
@click.option("--config", "-c", default=Path.home().joinpath(".yabu_presets.json"))
@click.pass_context
def cli(ctx: click.Context, config):
    ctx.ensure_object(dict)
    ctx.obj['config'] = config
    pass

@cli.command()
@click.pass_obj
def presets(obj):
    handler = CommandHandler(obj['config'])
    try:
        for preset in handler.list_presets():
            print(preset)
    except FileNotFoundError:
        print(f"Uh-Oh! Your config file appears to be missing: '{obj['config']}'")
    except ValueError:
        print(f"The path exists, it doesn't seem to be a .json file though: '{obj['config']}'")


@cli.command()
@click.option("--force", "-f", default=False)
@click.option("--keep", "-k", default=False)
@click.argument("preset")
@click.pass_obj
def backup(obj, preset, force, keep):
    print("Creating backups...")
    handler = CommandHandler(obj['config'])
    finished = False
    while not finished:
        backup_generator = handler.create_backups(preset, force, keep)
        try:
            print("The following backups were created: ")
            for backup in backup_generator:
                print(backup)
        except PresetNotFoundException:
            print(f"The requested preset '{obj['location']}' is not found.")
        except TargetNotFoundException as e:
            
            print(f"Backup Failed:\n\tTarget not found:\n\tTarget: {e.target}\n\tDestination: {e.destination}")
        except DestinationNotFoundException as e:
            print(f"Backup Failed:\n\Destination not found:\n\tTarget: {e.target}\n\tDestination: {e.destination}")
        except BackupHashException as e:
            print(f"Backup Failed:\n\tBackup hash matched latest backup in destination path.\n\tTarget: {e.target}\n\tDestination: {e.destination}")
        except FormatException as e:
            print(f"Backup Failed:\n\tBackup format unsupported\n\tTarget: {e.target}\n\Destination: {e.destination}")
        except StopIteration:
            finished = True


@cli.command()
@click.option("--path", "-p", default=False)
@click.argument("location")
@click.pass_obj
def restore(obj, location: str, path: bool):
    handler = CommandHandler(obj['config'])
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
    handler.restore_backup(location, selected_backup)

@cli.command()
@click.argument("preset")
def modify(preset):
    print(f"modifying the preset '{preset}'")

if __name__ == "__main__":
    cli()