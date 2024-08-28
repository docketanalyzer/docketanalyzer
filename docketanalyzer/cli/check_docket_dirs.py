import click
from docketanalyzer import load_docket_index


@click.command()
def check_docket_dirs():
    """
    Sanity check for unindexed docket data in DA_DATA_DIR.

    This command scans for any docket data in DA_DATA_DIR that might have been
    added manually and missed by the primary indexing process. It's not the
    main method for indexing and should rarely be necessary.

    Use only if you suspect local data hasn't been properly indexed.

    Usage:
    da check-dockets
    """
    index = load_docket_index()
    index.check_docket_dirs()
    print(f"Total dockets indexed: {index.table.count()}")
