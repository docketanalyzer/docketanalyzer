import pandas as pd
from pathlib import Path
import simplejson as json
from docketanalyzer import ObjectManager, json_default, to_int


class Document:
    def __init__(self, manager, entry_number, attachment_number=None):
        self.manager = manager
        self.entry_number = to_int(entry_number)
        self.attachment_number = to_int(attachment_number)

    @property
    def name(self):
        return self.manager.get_document_name(self.entry_number, self.attachment_number)
    
    @property
    def pdf_path(self):
        return self.manager.get_document_path(self.entry_number, self.attachment_number)
    
    @property
    def ocr_path(self):
        return self.manager.get_document_path(self.entry_number, self.attachment_number, ocr=True)

    @property
    def pdf_available(self):
        return self.pdf_path.exists()
    
    @property
    def ocr_available(self):
        return self.ocr_path.exists()

    @property
    def data(self):
        ocr_path = self.ocr_path
        if ocr_path.exists():
            return json.loads(ocr_path.read_text())

    @property
    def pages(self):
        data = self.data
        if data:
            return data.get('pages')
    
    def extract_pages(self, overwrite=False, max_pages=None):
        from docketanalyzer import extract_pages
        pdf_path, ocr_path = self.pdf_path, self.ocr_path
        do_ocr = pdf_path.exists() and (overwrite or not ocr_path.exists())
        if not do_ocr and ocr_path.exists():
            old_max_pages = self.data.get('max_pages', None)
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

    def purchase(self):
        if self.court == 'psc':
            raise ValueError("Cannot purchase documents for cases on the demo site")
        juri = self.manager.juri
        court = self.manager.court
        pdf_path = self.pdf_path
        entry_number, attachment_number = self.entry_number, self.attachment_number
        if not pdf_path.exists():
            pacer_case_id = self.manager.pacer_case_id
            if pacer_case_id:
                docket_json = self.manager.docket_json
                if docket_json:
                    for entry in docket_json['docket_entries']:
                        if to_int(entry['document_number']) == int(entry_number):
                            if attachment_number is None:
                                data = juri.purchase_document(pacer_case_id, entry['pacer_doc_id'], court)
                            else:
                                data = juri.purchase_attachment(
                                    pacer_case_id, entry['pacer_doc_id'],
                                    attachment_number, court,
                                )
                            if data['status'] != 'success':
                                print(f"Error purchasing document: {data['status']}")
                            else:
                                pdf_path.write_bytes(data['file'])
                            return data['status']
                            break


class DocketManager(ObjectManager):
    batch_attributes = [
        'header',
        'parties',
        'counsel',
        'get_entries',
        'entries',
        'entry_labels',
        'entry_spans',
        'docs',
        'idb_rows',
    ]

    @property
    def docket_id(self):
        return self.id

    @property
    def court(self):
        return self.docket_id.split('__')[0]
    
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
    def label_paths(self):
        return list(self.dir.glob('labels.*.csv'))

    @property
    def span_paths(self):
        return list(self.dir.glob('spans.*.csv'))

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
        else:
            return self.dir / f'doc.pdf.{name}.pdf'

    @property
    def pdf_paths(self):
        return list(self.dir.glob('doc.pdf.*.pdf'))
    
    @property
    def ocr_paths(self):
        return list(self.dir.glob('doc.ocr.*.json'))
    
    @property
    def pdf_docs(self):
        for path in self.pdf_paths:
            entry_number, attachment_number = self.parse_document_path(path)
            yield Document(self, entry_number, attachment_number)

    @property
    def ocr_docs(self):
        for path in self.ocr_paths:
            entry_number, attachment_number = self.parse_document_path(path)
            yield Document(self, entry_number, attachment_number)

    @property
    def all_docs(self):
        data = []
        entries = self.get_entries(process_text=True).dropna(subset=['entry_number'])
        for row in entries.to_dict('records'):
            data.append(Document(self, row['entry_number'], None))
            for attachment_section in row['attachments']:
                for attachment in attachment_section['attachments']:
                    data.append(Document(self, row['entry_number'], attachment['attachment_number']))
        return data

    def document(self, entry_number, attachment_number=None):
        return Document(self, entry_number, attachment_number)

    @property
    def juri(self):
        return self.index.juri

    def add_docket_html(self, html, skip_duplicates=True, add_to_index=True):
        self.dir.mkdir(parents=True, exist_ok=True)
        html_paths = list(self.docket_html_paths)
        if skip_duplicates and len(html_paths) > 0:
            for path in html_paths:
                if html == path.read_text():
                    print(f"Skipping duplicate docket html for {self.docket_id}")
                    return
        path = self.dir / f'pacer.{len(html_paths)}.html'
        path.write_text(html)
        if add_to_index:
            self.add_to_index()

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
        else:
            self.add_to_index()

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

    @property
    def tasks(self):
        from docketanalyzer import load_tasks
        return {
            k: v(index=self.index, selected_ids=[self.docket_id]) 
            for k, v in load_tasks().items()
        }
