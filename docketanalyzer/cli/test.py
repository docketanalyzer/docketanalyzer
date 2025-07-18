import subprocess

import click

from docketanalyzer import BASE_DIR, load_docket_index


@click.command(context_settings=dict(ignore_unknown_options=True))
@click.option("--setup-pacer", is_flag=True, help="Setup PACER fixtures. Skips tests.")
@click.option("--path", "-p", default=".", help="Optional relative path to test.")
@click.argument("args", nargs=-1, type=click.UNPROCESSED)
def test(setup_pacer, path, args):
    """Run or setup tests."""
    package_dir = BASE_DIR.parent.resolve()
    if setup_pacer:
        data_dir = package_dir / "tests" / "fixtures" / "data"
        data_dir.mkdir(parents=True, exist_ok=True)
        index = load_docket_index(data_dir)
        print(index)
    else:
        cmd = ["pytest", path]
        cmd.extend(args or ["-vv"])
        subprocess.run(cmd, check=True, cwd=str(package_dir))
