import subprocess
import sys

import click

from docketanalyzer import BASE_DIR, load_docket_index


@click.command(context_settings=dict(ignore_unknown_options=True))
@click.argument("path", default="", type=str)
@click.option("--markers", "-m", default=None, help="Optional pytest markers.")
@click.option("--setup-pacer", is_flag=True, help="Setup PACER fixtures. Skips tests.")
@click.option("--setup-recap", is_flag=True, help="Setup RECAP fixtures. Skips tests.")
def test(path, markers, setup_pacer, setup_recap):
    """Run or setup tests."""
    package_dir = BASE_DIR.parent.resolve()
    if setup_pacer or setup_recap:
        sys.path.insert(0, str(package_dir))
        from tests.conftest import (
            SAMPLE_DOCKET_ID1,
            SAMPLE_DOCKET_ID2,
            TEST_DATA_DIR,
        )

        TEST_DATA_DIR.mkdir(parents=True, exist_ok=True)

        index = load_docket_index(TEST_DATA_DIR)
        for docket_id in [SAMPLE_DOCKET_ID1, SAMPLE_DOCKET_ID2]:
            manager = index[docket_id]
            if setup_recap:
                manager.download_recap_data()
            if setup_pacer:
                manager.purchase_docket()
                manager.parse_docket()
                manager.purchase_document(entry_number=1)
                manager.purchase_document(
                    entry_number=1, attachment_number=1, suppress_errors=True
                )
            doc_path = manager.get_pdf_path(entry_number=1)
            manager.apply_ocr(doc_path)
            attachment_path = manager.get_pdf_path(entry_number=1, attachment_number=1)
            if attachment_path.exists():
                manager.apply_ocr(attachment_path)
    else:
        cmd = ["pytest", path, "-vv"]
        if markers:
            cmd.extend(["-m", markers])
        subprocess.run(cmd, check=True, cwd=str(package_dir))
