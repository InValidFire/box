import os, sys

from pathlib import Path
from itertools import product

import backup as lib


def print_divider(symbol: str = "-"):
	print(symbol * int(os.get_terminal_size().columns/len(symbol)))  # keeps it from overflowing

def backup_main(args: list):  # TODO: rewrite to have prettier output.
    """Create backups from the terminal."""
    
    output = {}
    try:
        backup_data = lib.StorageRoot().get_file(".backup_data.json").read_json()
        targets = backup_data[args[0]]['targets']
        destinations = backup_data[args[0]]["destinations"]
        output = {}
        for target, destination in product(targets, destinations):
            if destination not in output:
                output[destination] = {}
            if not Path(target).exists():
                print(f"cannot find '{target}'")
                output[destination][target] = "failed to find target."
                continue
            print(f"backing up '{target}'")
            try:
                storage = lib.StorageRoot(Path(destination))
                bm = lib.BackupManager(Path(target), storage=storage)
                output[destination]["status"] = "found!"
            except FileNotFoundError:
                print(f"cannot find '{destination}'")
                output[destination]["status"] = "failed to find destination."
                continue
            try:
                bm.create_backup()
                bm.delete_excess_backups(backup_data[args[0]]["max_count"])
                print(f"created backup to '{destination}'")
                output[destination][target] = "backed up successfully!"
            except FileExistsError:
                print("this backup already exists, skipping.")
                output[destination][target] = "backup already exists... skipped."
        print_divider()
        for i, destination in enumerate(output):
            print(f"{Path(destination).stem} - {output[destination]['status']}")
            for target in output[destination]:
                if target == "status":
                    continue
                print(f"\t{Path(target).stem}")
                print(f"\t\t{output[destination][target]}")
    # except IndexError:
    #     print("Please indicate which backup preset to run.")
    except KeyError:
        print("Backup preset not found.")
    except FileNotFoundError:
        print("'.backup_data.json' file not found.")
    # except BaseException as e:
    #     print("Error loading data.")

def restore_main(args: list):
    """Restore backups from the terminal."""
    from pathlib import Path
    from itertools import product
    import hashlib, cmd, shutil

    # load data from JSON
    try:
        backup_data = lib.StorageRoot().get_file(".backup_data.json").read_json()
    except FileNotFoundError:
        print("'.backup_data.json' file not found.")
        return
    try:
        targets = backup_data[args[0]]['targets']
    except KeyError:
        print("Backup preset not found.")
        return
    except IndexError:
        print("Please indicate which backup preset to run.")
    destinations = backup_data[args[0]]["destinations"]

    # load backup choices into a list
    choices = []
    hashes = []
    for target, destination in product(targets, destinations):
        print(f"reading '{Path(target).name}' backups from '{destination}'")
        try:
            storage = lib.StorageRoot(Path(destination))
            bm = lib.BackupManager(Path(target), storage=storage)
        except FileNotFoundError:
            print(f"cannot find {destination}")
            continue
        for backup in bm.get_backups():
            md5_hash = hashlib.md5(backup.path.read_bytes()).hexdigest()
            if md5_hash not in hashes:
                hashes.append(hashlib.md5(backup.path.read_bytes()).hexdigest())
                choices.append({"backup": backup, "date": bm.get_backup_date(backup), "bm": bm, "hash": hashlib.md5(backup.path.read_bytes()).hexdigest()})
    choices.sort(key=lambda x: x["date"])
    choices.reverse()
    
    # print choices
    print_divider()
    print("Available Backups: (CTRL-C to cancel)")
    for i, choice in enumerate(choices):
        items = [f"{i}.", choice["backup"].path.name.split(choice["bm"].separator)[0], f"[{choice['hash']}]", f"{str(choice['date'])}"]
        cmd.Cmd().columnize(items, displaywidth=shutil.get_terminal_size().columns)  # this method is undocumented.

    #  restore chosen backup
    try:
        choice = int(input("Which backup would you like to restore? "))
        choices[choice]['bm'].restore_backup(choices[choice]['backup'])
    except KeyboardInterrupt:
        print("\nAborting!")

if __name__ == "__main__":
    backup_main(sys.argv[1:])