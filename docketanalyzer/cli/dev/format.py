import os

import click

from docketanalyzer import BASE_DIR


@click.command("format")
@click.option("--no-fix", is_flag=True, help="Check for formatting without fixing.")
def format_command(no_fix):
    """Run lint and code format check."""
    fix = "--fix" if not no_fix else ""
    cmd = (
        f"ruff format {BASE_DIR.parent.resolve()} && "
        f"ruff check {fix} {BASE_DIR.parent.resolve()}"
    )
    os.system(cmd)
