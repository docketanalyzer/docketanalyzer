import os
import click
from docketanalyzer import DocketManager


@click.command('open')
@click.argument('docket_id')
def open_command(docket_id):
    cmd = f'open {DocketManager(docket_id).dir}'
    os.system(cmd)
