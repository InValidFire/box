import os
import sys

from pathlib import Path
from itertools import product

import backup_manager as lib
import argparse
import shutil
import hashlib
import cmd


def print_divider(symbol: str = "-"):
    print(symbol * int(os.get_terminal_size().columns/len(symbol)))


def backup(targets: list[str], destinations: list[str]):
    output = {}
    for target, destination in product(targets, destinations):
        if destination['path'] not in output:
            output[destination['path']] = {}
        if not Path(target).exists():
            print(f"cannot find '{target}'")
            output[destination['path']][target] = "failed to find target."
            continue
        print(f"backing up '{target}'")
        try:
            storage = lib.StorageRoot(Path(destination['path']))
            bm = lib.BackupManager(Path(target), storage=storage)
            output[destination['path']]['status'] = "found!"
        except FileNotFoundError:
            print(f"cannot find '{destination['path']}'")
            output[destination['path']]['status'] = "failed to find destination."
            continue
        try:
            bm.create_backup()
            bm.delete_excess_backups(destination['max_count'])
            print(f"created backup to '{destination['path']}'")
            output[destination['path']][target] = "backed up successful!"
        except FileExistsError:
            print("this backup already exists, skipping.")
            output[destination['path']
                   ][target] = "backup already exists... skipped."
        print_divider()
        for destination in output:
            print(
                f"{Path(destination).stem} - {output[destination]['status']}")
            for target in output[destination]:
                if target == "status":
                    continue
                print(f"\t{Path(target).stem}")
                print(f"\t\t{output[destination][target]}")


def restore(targets: list[str], destinations: list[str]):
    # load backup choices into a list
    choices = []
    hashes = []
    for target, destination in product(targets, destinations):
        print(
            f"reading '{Path(target).name}' backups from '{destination['path']}'")
        try:
            storage = lib.StorageRoot(Path(destination['path']))
            bm = lib.BackupManager(Path(target), storage=storage)
        except FileNotFoundError:
            print(f"cannot find {destination['path']}")
            continue
        for backup in bm.get_backups():
            md5_hash = hashlib.md5(backup.path.read_bytes()).hexdigest()
            if md5_hash not in hashes:
                hashes.append(hashlib.md5(
                    backup.path.read_bytes()).hexdigest())
                choices.append({"backup": backup, "date": bm.get_backup_date(
                    backup), "bm": bm, "hash": hashlib.md5(backup.path.read_bytes()).hexdigest()})
            else:
                print(
                    f"duplicate hash '{md5_hash}' found at path '{backup.path}'")
    choices.sort(key=lambda x: x["date"])
    choices.reverse()

    # print choices
    print_divider()
    print("Available Backups: (CTRL-C to cancel)")
    for i, choice in enumerate(choices):
        items = [f"{i}.", choice["backup"].path.name.split(choice["bm"].separator)[
            0], f"[{choice['hash']}]", f"{str(choice['date'])}"]
        # this method is undocumented.
        cmd.Cmd().columnize(items, displaywidth=shutil.get_terminal_size().columns)

    #  restore chosen backup
    try:
        choice = int(input("Which backup would you like to restore? "))
        choices[choice]['bm'].restore_backup(choices[choice]['backup'])
    except KeyboardInterrupt:
        print("\nAborting!")
        sys.exit(4)


def main():
    # setup

    # Exit Codes:
    #   0 - exited successfully
    #   1 - .backup_data.json file not found.
    #   2 - backup preset not found.
    #   3 - .backup_data.json formatted incorrectly.
    #   4 - backup restoration aborted

    parser = argparse.ArgumentParser(
        description="Backup utility by InValidFire")
    parser.add_argument("preset", type=str)
    parser.add_argument("--restore", "-r", action="store_true")

    args = parser.parse_args()

    try:
        presets = lib.StorageRoot().get_file(".backup_data.json").read_json()
    except FileNotFoundError:
        print(".backup_data.json file not found.")
        sys.exit(1)

    try:
        preset = presets[args.preset]
    except KeyError:
        print("Backup preset not found.")
        sys.exit(2)

    try:
        targets = preset['targets']
        destinations = preset['destinations']
    except KeyError:
        print(".backup_data.json formatted incorrectly.")
        sys.exit(3)

    if not args.restore:
        backup(targets, destinations)
    else:
        restore(targets, destinations)


if __name__ == "__main__":
    main()
