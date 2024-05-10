import click
from .configure import configure
from .check_dockets import check_dockets
from .check_idb import check_idb, check_idb_command
from .open import open_command


@click.group()
def cli():
    pass


cli.add_command(configure)
cli.add_command(check_dockets)
cli.add_command(check_idb_command)
cli.add_command(open_command)
