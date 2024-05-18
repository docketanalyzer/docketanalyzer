import click
from docketanalyzer import DocketIndex


@click.command()
def check_dockets():
    """
    Checks and updates the core dataset for indexing all dockets in the DA_DATA_DIR.
    """
    index = DocketIndex()
    index.check_docket_dirs()
    print(f"Total dockets: {len(index.dataset)}")
