from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import numpy as np
import pandas as pd
import simplejson as json
from tqdm import tqdm
from docketanalyzer.cli.check_idb import check_idb
from docketanalyzer.utils import timeout
from .task import DocketTask


class ParseDockets(DocketTask):
    """
    Parse the downloaded html dockets into json format.
    """
    name = 'parse-dockets'
    batch_size = 1000

    def process_row(self, row):
        manager = self.index[row.docket_id]
        manager.parse_docket()


class FindIDBEntries(DocketTask):
    """
    Match docket to idb entries.
    """
    name = 'find-idb-entries'
    batch_size = 5000
    depends_on = ['parse-dockets']
    data_cols = [('idb_rows', 'str'), ('idb_match', 'str')]

    def prepare(self):
        check_idb()

    def get_alternate_id(self, docket_id):
        docket_json = self.index[docket_id].docket_json
        if docket_json:
            alternate_id = (
                docket_id.split('__')[0] + '__' +
                docket_id.split('_')[-1] + '__' +
                str(docket_json['date_filed'])
            )
            return alternate_id
        return None

    def process(self, batch):
        data = batch.pandas('docket_id')
        data['alternate_id'] = None
        data['idb_match'] = 'none'
        idb_matches = self.index.idb_dataset.filter(docket_id__in=data['docket_id']).pandas('docket_id', 'idb_row')
        if not len(idb_matches):
            idb_matches = pd.DataFrame(columns=['docket_id', 'idb_row'])
        idb_matches = idb_matches.groupby('docket_id')['idb_row'].apply(list)
        data = data.merge(idb_matches, on='docket_id', how='left')
        data.loc[data['idb_row'].notnull(), 'idb_match'] = 'docket_id'
        data.loc[data['idb_row'].isnull(), 'alternate_id'] = data[data['idb_row'].isnull()]['docket_id'].apply(self.get_alternate_id)
        idb_matches = self.index.idb_dataset.filter(alternate_id__in=data['alternate_id'].dropna()).pandas('alternate_id', 'idb_row')
        if not len(idb_matches):
            idb_matches = pd.DataFrame(columns=['alternate_id', 'idb_row'])
        idb_matches = idb_matches.groupby('alternate_id')['idb_row'].apply(list)
        data.loc[data['idb_row'].isnull(), 'idb_row'] = data[data['idb_row'].isnull()]['alternate_id'].map(idb_matches)
        data.loc[data['idb_row'].notnull() & data['alternate_id'].notnull(), 'idb_match'] = 'alternate_id'
        data = {x['docket_id']: x for x in data.to_dict(orient='records')}
        updates = []
        for row in batch:
            idb_rows = data[row.docket_id]['idb_row']
            row.idb_rows = None if not isinstance(idb_rows, list) else json.dumps(idb_rows)
            row.idb_match = data[row.docket_id]['idb_match']
            updates.append(row)
        if updates:
            self.index.dataset.django_model.objects.bulk_update(updates, ['idb_rows', 'idb_match'])


class AddHeaders(DocketTask):
    """
    Adds header data to index.header_dataset.
    """
    name = 'add-headers'
    batch_size = 200000
    depends_on = ['parse-dockets']

    def post_reset(self, selected_ids):
        if selected_ids is None:
            self.index.header_dataset.delete(quiet=True)
            self.cache = {}
        else:
            self.index.header_dataset.filter(docket_id__in=selected_ids).delete()

    def process(self, batch):
        docket_ids = batch.pandas('docket_id')['docket_id'].tolist()
        try:
            self.index.header_dataset.filter(docket_id__in=docket_ids).delete()
        except AttributeError:
            pass
        headers = self.index.make_batch([x.docket_id for x in list(batch)]).headers
        self.index.header_dataset.add(headers)


class AddEntries(DocketTask):
    """
    Adds entries to index.entry_dataset.
    """
    name = 'add-entries'
    batch_size = 20000
    depends_on = ['parse-dockets']

    def post_reset(self, selected_ids):
        if selected_ids is None:
            self.index.entry_dataset.delete(quiet=True)
            self.cache = {}
        else:
            self.index.entry_dataset.filter(docket_id__in=selected_ids).delete()

    def process(self, batch):
        docket_ids = batch.pandas('docket_id')['docket_id'].tolist()
        try:
            self.index.entry_dataset.filter(docket_id__in=docket_ids).delete()
        except AttributeError:
            pass
        entries = self.index.make_batch([x.docket_id for x in list(batch)]).get_entries(add_shuffle_number=True)
        self.index.entry_dataset.add(entries)


class AddPartiesAndCounsel(DocketTask):
    """
    Adds parties to index.party_dataset and counsel to index.counsel_dataset.
    """
    name = 'add-parties-and-counsel'
    batch_size = 20000
    workers = None
    depends_on = ['parse-dockets']

    def post_reset(self, selected_ids):
        if selected_ids is None:
            self.index.party_dataset.delete(quiet=True)
            self.index.counsel_dataset.delete(quiet=True)
            self.cache = {}
        else:
            self.index.party_dataset.filter(docket_id__in=selected_ids).delete()
            self.index.counsel_dataset.filter(docket_id__in=selected_ids).delete()

    def process(self, batch):
        docket_ids = batch.pandas('docket_id')['docket_id'].tolist()
        try:
            self.index.party_dataset.filter(docket_id__in=docket_ids).delete()
        except AttributeError:
            pass
        try:
            self.index.counsel_dataset.filter(docket_id__in=docket_ids).delete()
        except AttributeError:
            pass
        parties, counsel = self.index.make_batch([x.docket_id for x in list(batch)]).parties_and_counsel
        self.index.party_dataset.add(parties)
        self.index.counsel_dataset.add(counsel)


class OCRDocuments(DocketTask):
    """
    OCR any case documents.
    """
    name = 'ocr-documents'
    batch_size = 5000
    depends_on = ['parse-dockets']
    overwrite = False

    def process_row(self, row):
        manager = self.index[row.docket_id]
        for pdf_path in manager.pdf_paths:
            entry_number, attachment_number = manager.parse_document_path(pdf_path)
            manager.ocr_document(entry_number, attachment_number, overwrite=self.overwrite)
   