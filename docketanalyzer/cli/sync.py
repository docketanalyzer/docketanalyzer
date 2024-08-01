import click
from docketanalyzer import load_docket_index


@click.command()
@click.option('--path', '-p', default='', help='Path to sync')
@click.option('--delete', is_flag=True, help='Add the delete flag to CLI command')
@click.option('--exact-timestamps', '-e', is_flag=True, help='Use exact timestamps for comparison')
@click.option('--exclude', default=None, help='Exclude pattern')
def push(path, delete, exact_timestamps, exclude):
    """
    Push data from the DA_DATA_DIR to the S3 bucket.
    """
    index = load_docket_index()
    index.push(path, delete=delete, exact_timestamps=exact_timestamps, exclude=exclude, confirm=True)


@click.command()
@click.option('--path', '-p', default='', help='Path to sync')
@click.option('--delete', is_flag=True, help='Add the delete flag to CLI command')
@click.option('--exact-timestamps', '-e', is_flag=True, help='Use exact timestamps for comparison')
@click.option('--exclude', default=None, help='Exclude pattern')
def pull(path, delete, exact_timestamps, exclude):
    """
    Pull data from the S3 bucket to the DA_DATA_DIR.
    """
    index = load_docket_index()
    index.pull(path, delete=delete, exact_timestamps=exact_timestamps, exclude=exclude, confirm=True)
