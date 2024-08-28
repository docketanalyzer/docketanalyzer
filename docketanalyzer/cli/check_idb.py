import click
from docketanalyzer import IDB


@click.command('check-idb')
@click.option('--reset', is_flag=True, help="Scrap any existing data and start fresh.")
@click.option('--skip-db', is_flag=True, help="Skip updating the database.")
def check_idb(reset, skip_db):
    """
    Download, preprocess, and index FJC's Integrated Database (IDB) court records.

    This command handles the Integrated Database (IDB) from the Federal Judicial Center (FJC),
    which contains comprehensive data on federal court cases. The command performs the following steps:
    1. Downloads the raw IDB data if not already present
    2. Preprocesses the data to fit the required format
    3. Adds the processed data to your database

    The IDB is a valuable resource for analyzing trends and patterns in federal court cases,
    providing researchers and analysts with detailed information on case filings and outcomes.

    Options:
    --reset: If set, removes any existing IDB data and starts the process from scratch.
             Use this option if you want to ensure you have the most up-to-date data.

    --skip-db: If set, the command will download and preprocess the data but will not update the database.

    Example usage:
    da check-idb  # Normal operation
    da check-idb --reset  # Start fresh with new data
    da check-idb --skip-db # Download and preprocess data but skip updating the database
    """
    idb = IDB(skip_db=skip_db)
    if reset:
        idb.reset()
    idb.update()
