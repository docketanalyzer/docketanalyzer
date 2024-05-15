import click
import docketanalyzer


@click.command()
@click.option('--reset', is_flag=True)
def configure(reset):
    docketanalyzer.config.update(reset=reset)
