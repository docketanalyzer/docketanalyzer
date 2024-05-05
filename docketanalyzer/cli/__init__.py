import click
from .hello import hello


@click.group()
def cli():
    pass


cli.add_command(hello)
