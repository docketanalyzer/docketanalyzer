import click

from .configure import configure
from .format import format_command
from .test import test, setup_tests
from .sync import push, pull
from .open import open_command
from .build import build


@click.group()
def cli():
    """Docket Analyzer CLI."""
    pass


cli.add_command(configure)
cli.add_command(format_command)
cli.add_command(test)
cli.add_command(setup_tests)
cli.add_command(push)
cli.add_command(pull)
cli.add_command(open_command)
cli.add_command(build)
