import click

from .build import build
from .format import format_command
from .test import test


@click.group()
def dev():
    """Application CLI."""
    pass


dev.add_command(build)
dev.add_command(format_command)
dev.add_command(test)
