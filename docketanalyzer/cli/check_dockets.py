import click
from docketanalyzer import DocketIndex


@click.command()
def check_dockets():
    """
    Adds any missing docket_ids in DA_DATA_DIR to index.dataset.
    """
    index = DocketIndex()
    index.check_docket_dirs()
    print(f"Total dockets: {len(index.dataset)}")
