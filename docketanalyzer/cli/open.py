import os

import click

from .. import load_docket_index


@click.command("open")
@click.argument("docket_id", default="")
def open_command(docket_id):
    """Open the directory of for given docket_id if not provided.

    If no docket_id is provided, a random docket from the index will be selected.

    Example usage:
    da open azd__2_17-cr-00384
    """
    index = load_docket_index()
    if not docket_id:
        docket_id = index.table.sample(1).pandas("docket_id")["docket_id"][0]
    manager = index[docket_id]
    cmd = f"open {manager.dir}"
    os.system(cmd)
