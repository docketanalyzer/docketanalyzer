from pathlib import Path
import simplejson as json
from docketanalyzer.utils import DATA_DIR


class DocketManager():
    def __init__(self, docket_id, data_dir=DATA_DIR):
        self.docket_id = docket_id
        self.data_dir = Path(data_dir)
        self.cache = {}

    @property
    def dir(self):
        return self.data_dir / 'dockets' / 'data' / self.docket_id

    @property
    def docket_html_paths(self):
        return list(self.dir.glob('pacer.*.html'))

    def add_docket_html(self, html):
        path = self.dir / f'pacer.{len(list(self.docket_html_paths))}.html'
        path.write_text(html)

    @property
    def docket_json_path(self):
        return self.dir / 'docket.json'

    @property
    def docket_json(self):
        if self.docket_json_path.exists():
            return json.loads(self.docket_json_path.read_text())

    def document_get_name(self, entry_number, attachment_number=None):
        return f'{entry_number}_{attachment_number or 0}'

    def document_get_pdf_path(self, entry_number, attachment_number=None):
        name = self.document_get_name(entry_number, attachment_number)
        return self.dir / f'doc.pdf.{name}.pdf'

    def document_get_ocr_path(self, entry_number, attachment_number=None):
        name = self.document_get_name(entry_number, attachment_number)
        return self.dir / f'doc.ocr.{name}.json'
