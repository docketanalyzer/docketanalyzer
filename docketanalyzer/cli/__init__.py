import click
from .dev import dev_cli
from .configure import configure


@click.group()
def cli():
    pass


cli.add_command(dev_cli)
cli.add_command(configure)
