from pathlib import Path
import click

from yabu_cmd.controller import CommandHandler

@click.group()
@click.option("--config", "-c", default=Path.home().joinpath(".yabu_presets.json"))
@click.pass_context
def cli(ctx: click.Context, config):
    ctx.ensure_object(dict)
    ctx.obj['config'] = config
    pass

@cli.command()
@click.pass_obj
def list(obj):
    handler = CommandHandler(obj['config'])
    print(handler.list_presets())


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

if __name__ == "__main__":
    cli()