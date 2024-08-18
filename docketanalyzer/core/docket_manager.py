from copy import deepcopy
import pandas as pd
from pathlib import Path
import simplejson as json
from docketanalyzer import load_dataset
from docketanalyzer.utils import DATA_DIR, json_default, convert_int


class DocketManager():
    def __init__(self, docket_id, data_dir=DATA_DIR, local=False, index=None):
        self.docket_id = docket_id
        self.data_dir = Path(data_dir)
        self.local = local
        self.cache = {}
        if index is not None:
            self.cache['index'] = index

    @property
    def row(self):
        return self.dataset[self.docket_id]

    @property
    def status(self):
        return self.dataset.filter(docket_id=self.docket_id).get_first_as_dict()

    @property
    def index(self):
        if 'index' not in self.cache:
            from docketanalyzer import load_docket_index
            self.cache['index'] = load_docket_index(local=self.local)
        return self.cache['index']

    @property
    def dataset(self):
        return self.index.dataset

    @property
    def entry_dataset(self):
        return self.index.entry_dataset

    @property
    def doc_dataset(self):
        return self.index.doc_dataset

    @property
    def idb_dataset(self):
        return self.index.idb_dataset

    @property
    def juri(self):
        return self.index.juri

    @property
    def dir(self):
        return self.data_dir / 'dockets' / self.docket_id

    @property
    def docket_html_paths(self):
        return list(self.dir.glob('pacer.*.html'))

    @property
    def docket_json_path(self):
        return self.dir / 'pacer.json'

    @property
    def docket_json(self):
        if self.docket_json_path.exists():
            return json.loads(self.docket_json_path.read_text())

    @property
    def search_json_path(self):
        return self.dir / 'search.json'

    @property
    def search_json(self):
        if self.search_json_path.exists():
            return json.loads(self.search_json_path.read_text())

    @property
    def entries(self):
        if 'entries' not in self.cache:
            self.cache['entries'] = self.index.make_batch([self.docket_id]).entries
        return self.cache['entries']
    
    @property
    def entries_with_labels(self):
        if 'entries_with_labels' not in self.cache:
            self.cache['entries_with_labels'] =  self.index.make_batch([self.docket_id]).get_entries(add_predictions=True)
        return self.cache['entries_with_labels']
    
    @property
    def docs(self):
        if 'docs' not in self.cache:
            self.cache['docs'] = self.index.make_batch([self.docket_id]).docs
        return self.cache['docs']
    
    @property
    def header(self):
        if 'header' not in self.cache:
            self.cache['header'] = self.index.make_batch([self.docket_id]).headers.iloc[0].to_dict()
        return self.cache['header']
    
    @property
    def parties(self):
        if 'parties' not in self.cache:
            parties, counsel = self.index.make_batch([self.docket_id]).parties_and_counsel
            self.cache['parties'] = parties
            self.cache['counsel'] = counsel
        return self.cache['parties']
    
    @property
    def counsel(self):
        if 'counsel' not in self.cache:
            parties, counsel = self.index.make_batch([self.docket_id]).parties_and_counsel
            self.cache['parties'] = parties
            self.cache['counsel'] = counsel
        return self.cache['counsel']

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

    def get_document_name(self, entry_number, attachment_number=None):
        attachment_number = 0 if pd.isnull(attachment_number) else attachment_number
        return f'{int(entry_number)}_{int(attachment_number)}'

    def get_document_path(self, entry_number, attachment_number=None, ocr=False):
        name = self.get_document_name(entry_number, attachment_number)
        if ocr:
            return self.dir / f'doc.ocr.{name}.json'
        return self.dir / f'doc.pdf.{name}.pdf'
    
    def extract_document_text(self, entry_number, attachment_number=None, overwrite=False, max_pages=None):
        from docketanalyzer import extract_pages
        pdf_path = self.get_document_path(entry_number, attachment_number)
        ocr_path = self.get_document_path(entry_number, attachment_number, ocr=True)
        do_ocr = overwrite or not ocr_path.exists()
        if not do_ocr and ocr_path.exists():
            old_max_pages = json.loads(ocr_path.read_text()).get('max_pages', None)
            if old_max_pages is not None and (max_pages is None or old_max_pages < max_pages):
                do_ocr = True
        if do_ocr:
            pages = extract_pages(pdf_path, max_pages=max_pages)
            if pages is not None:
                data = {'pages': pages}
                if max_pages is not None:
                    data['max_pages'] = max_pages
                ocr_path.write_text(json.dumps(data, indent=2, default=json_default))
        return ocr_path

    def push(self, name=None, delete=False, exact_timestamps=True, exclude=None, confirm=False):
        args = {}
        if name is not None:
            args['include'] = name
            exclude = '*'
        self.index.push(path, delete, exact_timestamps, exclude, confirm=confirm, **args)

    def pull(self, name=None, delete=False, exact_timestamps=True, exclude=None, confirm=False):
        args = {}
        if name is not None:
            args['include'] = name
            exclude = '*'
        self.index.pull(self.dir, delete, exact_timestamps, exclude, confirm=confirm, **args)

    @property
    def tasks(self):
        from docketanalyzer import load_tasks
        return {
            k: v(dataset=self.dataset, selected_ids=[self.docket_id]) 
            for k, v in load_tasks().items()
        }

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
    
    def add_to_dataset(self):
        self.dataset.add(pd.DataFrame({'docket_id': [self.docket_id]}))

    def add_docket_html(self, html, skip_duplicates=True, add_to_dataset=True):
        self.dir.mkdir(parents=True, exist_ok=True)
        html_paths = list(self.docket_html_paths)
        if skip_duplicates and len(html_paths) > 0:
            for path in html_paths:
                if html == path.read_text():
                    print(f"Skipping duplicate docket html for {self.docket_id}")
                    return
        path = self.dir / f'pacer.{len(html_paths)}.html'
        path.write_text(html)
        if add_to_dataset:
            self.add_to_dataset()

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
        else:
            self.add_to_dataset()

    def parse_docket(self):
        juri = self.juri
        html_paths = list(sorted(self.docket_html_paths))
        if not html_paths:
            raise ValueError(f"No docket html found for {self.docket_id}")
        entries = []
        for html_path in html_paths:
            html = html_path.read_text()
            docket_parsed = juri.parse(html, self.court)
            if docket_parsed:
                entries += docket_parsed['docket_entries']
            else:
                raise ValueError(f"Docket {self.docket_id} could not be parsed")
        docket_parsed['docket_entries'] = entries
        self.docket_json_path.write_text(json.dumps(
            docket_parsed, indent=2, default=json_default,
        ))

    def purchase_document(self, entry_number, attachment_number=None):
        if self.court == 'psc':
            raise ValueError("Cannot purchase documents for cases on the demo site")
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
