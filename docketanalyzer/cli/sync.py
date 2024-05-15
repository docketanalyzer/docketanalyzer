import click
from docketanalyzer import S3Utility


def sync(path, delete, exact_timestamps, exclude, push=True):
    exclude = [] if exclude is None else exclude.split(',')
    exclude.append("*__pycache__*")

    s3 = S3Utility()
    args = dict(
        from_path=path, to_path=path, delete=delete,
        exact_timestamps=exact_timestamps,
        confirm=True, exclude=exclude,
    )
    if push:
        s3.push(**args)
    else:
        s3.pull(**args)


@click.command()
@click.option('--path', '-p', default='', help='Path to sync')
@click.option('--delete', is_flag=True, help='Add the delete flag to CLI command')
@click.option('--exact-timestamps', '-e', is_flag=True, help='Use exact timestamps for comparison')
@click.option('--exclude', default=None, help='Exclude pattern')
def push(path, delete, exact_timestamps, exclude):
    sync(path, delete, exact_timestamps, exclude, push=True)


@click.command()
@click.option('--path', '-p', default='', help='Path to sync')
@click.option('--delete', is_flag=True, help='Add the delete flag to CLI command')
@click.option('--exact-timestamps', '-e', is_flag=True, help='Use exact timestamps for comparison')
@click.option('--exclude', default=None, help='Exclude pattern')
def pull(path, delete, exact_timestamps, exclude):
    sync(path, delete, exact_timestamps, exclude, push=False)
