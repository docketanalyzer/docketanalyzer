import click
from .build import build
from .build_extension import build_extension
from .install_extension import install_extension


@click.group('dev')
def dev_cli():
    pass


dev_cli.add_command(build)
dev_cli.add_command(build_extension)
dev_cli.add_command(install_extension)
