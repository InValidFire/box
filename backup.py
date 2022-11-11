import json
import os
import sys

from pathlib import Path
from itertools import product

import backup_manager as lib
import argparse
import shutil
import hashlib
import cmd

MAJOR = 0
MINOR = 2
PATCH = 1

VERSION = ".".join([str(x) for x in [MAJOR, MINOR, PATCH]])


def print_divider(symbol: str = "-"):
    print(symbol * int(os.get_terminal_size().columns/len(symbol)))


def backup(targets: list[str], destinations: list[str], force=True, keep=False):
    output = {}  # holds data used in printing output to the user.
    for target, destination in product(targets, destinations):
        if destination['path'] not in output:
            output[destination['path']] = {}
        if not Path(target).exists():
            print(f"cannot find '{target}'")
            output[destination['path']][target] = "failed to find target."
            continue
        print(f"backing up '{target}'")
        try:
            storage_folder = Path(destination['path'])
            bm = lib.BackupManager(Path(target), storage_folder)
            output[destination['path']]['status'] = "found!"
        except FileNotFoundError:
            print(f"cannot find '{destination['path']}'")
            output[destination['path']]['status'] = "failed to find destination."
            continue
        try:
            bm.create_backup(force=force)
            if not keep:
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
            storage = Path(destination['path'])
            bm = lib.BackupManager(Path(target), storage)
        except FileNotFoundError:
            print(f"cannot find {destination['path']}")
            continue
        for backup in bm.get_backups():
            md5_hash = hashlib.md5(backup.read_bytes()).hexdigest()
            if md5_hash not in hashes:
                hashes.append(hashlib.md5(
                    backup.read_bytes()).hexdigest())
                choices.append({"backup": backup, "date": bm.get_backup_date(
                    backup), "bm": bm, "hash": hashlib.md5(backup.read_bytes()).hexdigest()})
            else:
                print(
                    f"duplicate hash '{md5_hash}' found at path '{backup}'")
    choices.sort(key=lambda x: x["date"])
    choices.reverse()

    # print choices
    print_divider()
    print("Available Backups: (CTRL-C to cancel)")
    for i, choice in enumerate(choices):
        items = [f"{i}.", choice["backup"].name.split(choice["bm"].separator)[
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
    #   1 - config file not found.
    #   2 - backup preset not found.
    #   3 - config file formatted incorrectly.
    #   4 - backup restoration aborted

    parser = argparse.ArgumentParser(
        description="Backup utility by InValidFire", prog="backup_cmd", )
    parser.add_argument("preset", type=str,
                        help="specifies which backup preset to run")
    parser.add_argument("--restore", "-r", action="store_true",
                        help="switch to restore a backup")
    parser.add_argument("--version", "-v", action="version",
                        version=f"{parser.prog} {VERSION} by InValidFire", help="print version information and exit")
    parser.add_argument("--force", "-f", action="store_true",
                        help="force backup creation even if it's already saved")
    parser.add_argument("--keep", "-k", action="store_true",
                        help="keep old backups beyond the max_count value")
    parser.add_argument("--config", type=Path, default=Path.home().joinpath(".storage").joinpath(".backup_data.json"), help="specify a custom path for the configuration file.")

    args = parser.parse_args()

    try:
        config_file = args.config
        print(f"reading config file '{config_file}'")
        with config_file.open("r+") as fp:
            presets = json.load(fp)
    except FileNotFoundError:
        print("config file not found.")
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
        print("config file formatted incorrectly.")
        sys.exit(3)

    if not args.restore:
        backup(targets, destinations, force=args.force, keep=args.keep)
    else:
        restore(targets, destinations)


if __name__ == "__main__":
    main()
