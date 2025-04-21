import subprocess

import click

from docketanalyzer import BASE_DIR


@click.command()
def test():
    """Run tests."""
    cmd = [
        "pytest",
        BASE_DIR.parent.resolve(),
        "-vv",
    ]
    subprocess.run(cmd, check=True)
