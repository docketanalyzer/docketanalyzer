import subprocess
import sys

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
        sys.path.insert(0, str(package_dir))
        from tests.conftest import (
            TEST_DATA_DIR,
            SAMPLE_DOCKET_ID1,
            SAMPLE_DOCKET_ID2,
        )

        TEST_DATA_DIR.mkdir(parents=True, exist_ok=True)

        index = load_docket_index(TEST_DATA_DIR)
        for docket_id in [SAMPLE_DOCKET_ID1, SAMPLE_DOCKET_ID2]:
            manager = index[docket_id]
            manager.purchase_docket()
            manager.parse_docket()
            manager.purchase_document(entry_number=1)
            manager.purchase_document(
                entry_number=1, attachment_number=1, suppress_errors=True
            )
    else:
        cmd = ["pytest", path]
        cmd.extend(args or ["-vv"])
        subprocess.run(cmd, check=True, cwd=str(package_dir))
