import click
from .check_dockets import check_dockets
from .check_idb import check_idb


@click.group()
def cli():
    pass


cli.add_command(check_dockets)
cli.add_command(check_idb)
