import click


@click.command()
def hello():
    """Hello."""
    click.echo("hello")
