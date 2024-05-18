from pathlib import Path
import simplejson as json
from docketanalyzer import load_dataset, JuriscraperUtility
from docketanalyzer.utils import DATA_DIR, json_default, convert_int


class DocketManager():
    def __init__(self, docket_id, data_dir=DATA_DIR, local=False):
        self.docket_id = docket_id
        self.data_dir = Path(data_dir)
        self.local = local
        self.cache = {}

    @property
    def row(self):
        return self.dataset[self.docket_id]

    @property
    def dataset(self):
        if 'dataset' not in self.cache:
            self.cache['dataset'] = load_dataset('dockets', pk='docket_id', local=self.local)
        return self.cache['dataset']

    @property
    def entry_dataset(self):
        if 'entry_dataset' not in self.cache:
            self.cache['entry_dataset'] = load_dataset('entries', pk='entry_id', local=self.local)
        return self.cache['entry_dataset']

    @property
    def doc_dataset(self):
        if 'doc_dataset' not in self.cache:
            self.cache['doc_dataset'] = load_dataset('docs', pk='doc_id', local=self.local)
        return self.cache['doc_dataset']

    @property
    def juri(self):
        if 'juri' not in self.cache:
            self.cache['juri'] = JuriscraperUtility()
        return self.cache['juri']

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

    @property
    def pdf_paths(self):
        return list(self.dir.glob('doc.pdf.*.pdf'))

    @property
    def ocr_paths(self):
        return list(self.dir.glob('doc.ocr.*.json'))

    def parse_document_path(self, path):
        path = Path(path)
        name = path.name.split('.')[-2]
        entry_number, attachment_number = name.split('_')
        entry_number, attachment_number = int(entry_number), int(attachment_number)
        attachment_number = attachment_number if attachment_number else None
        return entry_number, attachment_number

    def document_get_name(self, entry_number, attachment_number=None):
        return f'{entry_number}_{attachment_number or 0}'

    def get_document_path(self, entry_number, attachment_number=None, ocr=False):
        name = self.document_get_name(entry_number, attachment_number)
        if ocr:
            return self.dir / f'doc.ocr.{name}.json'
        return self.dir / f'doc.pdf.{name}.pdf'

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
            print(f"Consolidating multiple dockets not yet implemented: {self.docket_id}")
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
        pdf_path = self.get_document_path(entry_number, attachment_number)
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
                            return data['status']
                            break
