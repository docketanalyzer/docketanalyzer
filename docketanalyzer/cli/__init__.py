import click

from .configure import configure
from .dev import dev


@click.group()
def cli():
    """Docket Analyzer CLI."""
    pass


cli.add_command(configure)
cli.add_command(dev)
