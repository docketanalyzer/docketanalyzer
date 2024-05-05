import click
from .hello import hello
from .prepare_idb_dataset import prepare_idb_dataset


@click.group()
def cli():
    pass


cli.add_command(hello)
cli.add_command(prepare_idb_dataset)
