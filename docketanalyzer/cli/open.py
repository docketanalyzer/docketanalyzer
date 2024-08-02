import os
import click
from docketanalyzer import DocketManager


@click.command('open')
@click.argument('docket_id')
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
    cmd = f'open {DocketManager(docket_id).dir}'
    os.system(cmd)
