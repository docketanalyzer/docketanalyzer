import click

from .configure import configure
from .sync import push, pull
from .open import open_command
from .dev import dev


@click.group()
def cli():
    """Docket Analyzer CLI."""
    pass


cli.add_command(configure)
cli.add_command(push)
cli.add_command(pull)
cli.add_command(open_command)
cli.add_command(dev)
