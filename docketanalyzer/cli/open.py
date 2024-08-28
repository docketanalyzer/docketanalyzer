import os
import click
from docketanalyzer import load_docket_index


@click.command('open')
@click.argument('docket_id', default='')
def open_command(docket_id):
    """
    Open the directory of a specific docket in the system's file explorer.

    This command takes a docket ID and opens the corresponding docket directory
    in the default file explorer of your operating system. This is useful for
    quickly accessing the local files associated with a particular docket.

    Arguments:
    DOCKET_ID: The unique identifier of the docket to open.

    Example usage:
    da open azd__2_17-cr-00384  # Opens the directory for docket with ID azd__2_17-cr-00384
    """
    index = load_docket_index()
    if not docket_id:
        docket_id = index.table.sample(1).pandas('docket_id')['docket_id'][0]
    manager = index[docket_id]
    cmd = f'open {manager.dir}'
    os.system(cmd)
