import click
import docketanalyzer


@click.command()
def configure():
    docketanalyzer.config.update()
