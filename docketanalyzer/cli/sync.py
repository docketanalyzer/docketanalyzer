import click

from .. import load_docket_index


@click.command()
@click.argument("path", default="")
@click.option("--delete", is_flag=True, help="Add the delete flag to CLI command")
@click.option("--exact-timestamps", "-e", is_flag=True, help="Use exact timestamps")
@click.option("--exclude", default=None, help="Exclude pattern")
@click.option("--include", default=None, help="Include pattern")
@click.option("--skip-confirm", "-y", is_flag=True, help="Skip confirmation")
def push(path, delete, exact_timestamps, exclude, include, skip_confirm):
    """Push data from the specified PATH relative to your DATA_DIR to the S3 bucket.

    This command synchronizes data from the local directory specified by PATH
    to a predetermined S3 bucket. If PATH is not provided, it defaults to
    pushing all data from the DATA_DIR. To configure S3, run `da configure s3`.

    Example usage:
    da push /path/to/local/dir --exact-timestamps --exclude '*.html'
    """
    if delete:
        click.confirm(
            (
                "WARNING: You are pushing with the delete flag. This is not recommended"
                "as the S3 bucket is the primary data store. Are you sure you want to "
                "continue?"
            ),
            abort=True,
        )
    index = load_docket_index()
    exclude = None if exclude is None else exclude.split(",")
    include = None if include is None else include.split(",")
    index.push(
        path,
        delete=delete,
        exact_timestamps=exact_timestamps,
        exclude=exclude,
        include=include,
        confirm=not skip_confirm,
    )


@click.command()
@click.argument("path", default="")
@click.option("--delete", is_flag=True, help="Add the delete flag to CLI command")
@click.option("--exact-timestamps", "-e", is_flag=True, help="Use exact timestamps")
@click.option("--exclude", default=None, help="Exclude pattern")
@click.option("--include", default=None, help="Include pattern")
@click.option("--skip-confirm", "-y", is_flag=True, help="Skip confirmation")
def pull(path, delete, exact_timestamps, exclude, include, skip_confirm):
    """Pull data from the S3 bucket to the specified PATH relative to your DATA_DIR.

    This command synchronizes data from a predetermined S3 bucket to the local directory
    specified by PATH. If PATH is not provided, it defaults to pulling all data to the
    DATA_DIR. To configure S3, run `da configure s3`.

    Example usage:
    da pull /path/to/local/dir --exact-timestamps --exclude '*.html'
    """
    index = load_docket_index()
    exclude = None if exclude is None else exclude.split(",")
    include = None if include is None else include.split(",")
    index.pull(
        path,
        delete=delete,
        exact_timestamps=exact_timestamps,
        exclude=exclude,
        include=include,
        confirm=not skip_confirm,
    )
