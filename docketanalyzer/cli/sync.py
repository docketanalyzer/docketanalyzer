import click
from docketanalyzer import load_docket_index


@click.command()
@click.argument('path', default='')
@click.option('--delete', is_flag=True, help='Add the delete flag to CLI command')
@click.option('--exact-timestamps', '-e', is_flag=True, help='Use exact timestamps for comparison')
@click.option('--exclude', default=None, help='Exclude pattern')
@click.option('--include', default=None, help='Include pattern')
def push(path, delete, exact_timestamps, exclude, include):
    """
    Push data from the specified PATH relative to your DATA_DIR to the S3 bucket.

    This command synchronizes data from the local directory specified by PATH
    to a predetermined S3 bucket. If PATH is not provided, it defaults to
    pushing all data from the DATA_DIR. To configure S3, run `da configure s3`.

    Arguments:
    PATH: The local directory path to sync to S3. If not provided, syncs entire DA_DATA_DIR.

    Options:
    --delete: If set, will delete files in the S3 bucket that don't exist in the local directory.
    --exact-timestamps, -e: If set, uses exact timestamp comparisons instead of size and modified time.
    --exclude: Pattern to exclude files or directories from the sync process.

    Example usage:
    da push /path/to/local/dir --delete --exact-timestamps --exclude '*.tmp'
    """
    if delete:
        click.confirm('WARNING: You are pushing with the delete flag. This is not recommended as the S3 bucket is the primary data store. Are you sure you want to continue?', abort=True)
    index = load_docket_index()
    exclude = None if exclude is None else exclude.split(',')
    include = None if include is None else include.split(',')
    index.push(path, delete=delete, exact_timestamps=exact_timestamps, exclude=exclude, include=include, confirm=True)


@click.command()
@click.argument('path', default='')
@click.option('--delete', is_flag=True, help='Add the delete flag to CLI command')
@click.option('--exact-timestamps', '-e', is_flag=True, help='Use exact timestamps for comparison')
@click.option('--exclude', default=None, help='Exclude pattern')
@click.option('--include', default=None, help='Include pattern')
def pull(path, delete, exact_timestamps, exclude, include):
    """
    Pull data from the S3 bucket to the specified PATH relative to your DATA_DIR.

    This command synchronizes data from a predetermined S3 bucket to the local directory
    specified by PATH. If PATH is not provided, it defaults to pulling all data to the
    DATA_DIR. To configure S3, run `da configure s3`.

    Arguments:
    PATH: The local directory path to sync from S3. If not provided, syncs entire S3 bucket.

    Options:
    --delete: If set, will delete files in the local directory that don't exist in the S3 bucket.
    --exact-timestamps, -e: If set, uses exact timestamp comparisons instead of size and modified time.
    --exclude: Pattern to exclude files or directories from the sync process.

    Example usage:
    da pull /path/to/local/dir --delete --exact-timestamps --exclude '*.tmp'
    """
    index = load_docket_index()
    exclude = None if exclude is None else exclude.split(',')
    include = None if include is None else include.split(',')
    index.pull(path, delete=delete, exact_timestamps=exact_timestamps, exclude=exclude, include=include, confirm=True)