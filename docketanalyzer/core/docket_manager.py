from pathlib import Path
import simplejson as json
from docketanalyzer import load_dataset, JuriscraperUtility
from docketanalyzer.utils import DATA_DIR, json_default, convert_int


class DocketManager():
    def __init__(self, docket_id, data_dir=DATA_DIR, local=False):
        self.docket_id = docket_id
        self.data_dir = Path(data_dir)
        self.dataset = load_dataset('dockets', pk='docket_id', local=local)
        self.cache = {}

    @property
    def dir(self):
        return self.data_dir / 'dockets' / self.docket_id

    @property
    def docket_html_paths(self):
        return list(self.dir.glob('pacer.*.html'))

    def add_docket_html(self, html):
        self.dir.mkdir(parents=True, exist_ok=True)
        path = self.dir / f'pacer.{len(list(self.docket_html_paths))}.html'
        path.write_text(html)

    @property
    def docket_json_path(self):
        return self.dir / 'pacer.json'

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

    @property
    def court(self):
        return self.docket_id.split('__')[0]

    @property
    def pacer_case_id(self):
        if 'pacer_case_id' not in self.cache:
            candidates = self.juri.find_candidates(self.docket_id)
            self.cache['pacer_case_id'] = None
            if len(candidates):
                candidates = sorted(candidates, key=lambda x: len(x['docket_number']))
                self.cache['pacer_case_id'] = candidates[0]['pacer_case_id']
        return self.cache['pacer_case_id']

    def purchase_docket(self, update=False):
        if update:
            raise NotImplementedError("Updates not yet implemented")
        juri = self.juri
        if not self.docket_html_paths:
            if self.pacer_case_id:
                html, _ = juri.purchase_docket_with_pacer_case_id(
                    self.court, self.pacer_case_id,
                    show_parties_and_counsel=True,
                    show_terminated_parties=True,
                )
                self.add_docket_html(html)

    def parse_docket(self):
        juri = self.juri
        html_paths = self.docket_html_paths
        if len(html_paths) > 1:
            raise NotImplementedError("Consolidating multiple dockets not yet implemented")
        if html_paths:
            html = html_paths[0].read_text()
            docket_parsed = juri.parse(html, self.court)
            if docket_parsed:
                self.docket_json_path.write_text(json.dumps(
                    docket_parsed, indent=2, default=json_default,
                ))
            else:
                raise ValueError("Docket could not be parsed")

    def purchase_document(self, entry_number, attachment_number=None):
        juri = self.juri
        pdf_path = self.document_get_pdf_path(entry_number, attachment_number)
        if not pdf_path.exists():
            if self.pacer_case_id:
                docket_json = self.docket_json
                if docket_json:
                    for entry in docket_json['docket_entries']:
                        if convert_int(entry['document_number']) == int(entry_number):
                            if attachment_number is None:
                                data = juri.purchase_document(self.pacer_case_id, entry['pacer_doc_id'], self.court)
                            else:
                                data = juri.purchase_attachment(
                                    self.pacer_case_id, entry['pacer_doc_id'], 
                                    attachment_number, self.court,
                                )
                            if data['status'] != 'success':
                                print(f"Error purchasing document: {data['status']}")
                            else:
                                pdf_path.write_bytes(data['file'])
                            break

    @property
    def juri(self):
        if 'juri' not in self.cache:
            self.cache['juri'] = JuriscraperUtility()
        return self.cache['juri']
