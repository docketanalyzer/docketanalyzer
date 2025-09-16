import subprocess

import click

from docketanalyzer import env


@click.command()
def connect():
    """Open tunnel for local development."""
    cmd = [
        "ssh",
        "-N",
        "-o",
        "ExitOnForwardFailure=yes",
        "-L",
        "6543:127.0.0.1:5432",
        "-L",
        "9201:127.0.0.1:9200",
        env.SSH_HOST,
    ]

    subprocess.run(cmd, check=True)
