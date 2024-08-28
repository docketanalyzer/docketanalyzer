import click
from .build import build
from .configure import configure
from .check_docket_dirs import check_docket_dirs
from .check_idb import check_idb
from .open import open_command
from .sync import push, pull
from .tasks import tasks


@click.group()
def cli():
    pass


cli.add_command(configure)
cli.add_command(open_command)
cli.add_command(check_docket_dirs)
cli.add_command(check_idb)
cli.add_command(tasks)
cli.add_command(push)
cli.add_command(pull)
cli.add_command(build)