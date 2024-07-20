import os
import click
from docketanalyzer import DocketManager


@click.command('open')
@click.argument('docket_id')
def open_command(docket_id):
    """
    Provide a docket_id to open the docket directory in the explorer.
    """
    cmd = f'open {DocketManager(docket_id).dir}'
    os.system(cmd)
