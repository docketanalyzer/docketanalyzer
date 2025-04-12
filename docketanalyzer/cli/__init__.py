import click

from .format import format_command
from .test import test


@click.group()
def cli():
    """Application CLI."""
    pass


cli.add_command(format_command)
cli.add_command(test)
