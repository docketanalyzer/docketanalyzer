import subprocess

import click

from docketanalyzer import BASE_DIR


@click.command("format")
@click.option("--no-fix", is_flag=True, help="Check for formatting without fixing.")
def format_command(no_fix):
    """Run lint and code format check."""
    project_path = str(BASE_DIR.parent.resolve())

    subprocess.run(["ruff", "format", project_path])

    cmd = ["ruff", "check"]
    if not no_fix:
        cmd.append("--fix")
    cmd.append(project_path)
    subprocess.run(cmd)
