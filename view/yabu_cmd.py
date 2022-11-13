from pathlib import Path
import click

@click.group()
@click.option("--config", "-c", default=Path.home())
def cli():
    pass

@cli.command()
@click.option("--force", "-f", default=False)
@click.option("--keep", "-k", default=False)
@click.argument("preset")
def backup(preset, force, keep):
    print(f"creating a backup of '{preset}' | " + str(force) + " | " + str(keep))

@cli.command()
@click.argument("preset")
def restore(preset):
    print(f"restoring a backup of '{preset}'")

@cli.command()
@click.argument("preset")
def modify(preset):
    print(f"modifying the preset '{preset}'")