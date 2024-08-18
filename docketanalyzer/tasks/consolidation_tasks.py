import simplejson as json
from docketanalyzer.utils import json_default
from .task import DocketTask


class ConsolidateSearchDocket(DocketTask):
    """
    Consolidate search docket.
    """
    name = 'consolidate-search'
    batch_size = 20000
    depends_on = [
        'parse-dockets', 'find-idb-entries', 
        'label-predict-answer', 'label-predict-complaint',
        'label-predict-judgment', 'label-predict-minute-entry',
        'label-predict-motion', 'label-predict-notice',
        'label-predict-order', 'label-predict-stipulation'
    ]

    def process(self, batch):
        docket_ids = batch.pandas('docket_id', 'idb_rows')
        idb_rows = docket_ids.dropna(subset=['idb_rows'])
        idb_rows['idb_rows'] = idb_rows['idb_rows'].apply(json.loads)
        idb_rows = idb_rows.explode('idb_rows').rename(columns={'idb_rows': 'idb_row'})
        idb_data = self.index.idb_dataset.filter(idb_row__in=idb_rows['idb_row'].unique()).pandas()
        idb_data = idb_data.drop(columns=['id', 'court', 'docket_id', 'alternate_id'])
        idb_rows = idb_rows.merge(idb_data, on='idb_row', how='left')
        idb_rows = idb_rows.groupby('docket_id').apply(lambda x:
            x.to_dict('records')
        , include_groups=False).to_dict()

        docket_batch = self.index.make_batch(docket_ids['docket_id'].tolist())

        entries = docket_batch.get_entries(add_predictions=True)
        entries = entries.drop(columns=['entry_id'])
        entries = entries.groupby('docket_id').apply(lambda x:
            x.to_dict('records')
        , include_groups=False).to_dict()
  
        parties, counsel = docket_batch.parties_and_counsel
        counsel = counsel.drop(columns=['docket_id', 'attorney_id'])
        counsel = counsel.groupby('party_id').apply(lambda x:
            x.to_dict('records')
        , include_groups=False).to_dict()
        parties['counsel'] = parties['party_id'].apply(lambda x:
            counsel.get(x, [])
        )
        parties = parties.drop(columns=['party_id'])
        parties = parties.groupby('docket_id').apply(lambda x:
            x.to_dict('records')
        , include_groups=False).to_dict()

        headers = docket_batch.headers
        headers.index = headers['docket_id']
        headers = headers.to_dict('index')

        for row in batch:
            self.process_row(row,
                headers[row.docket_id],
                parties.get(row.docket_id, []),
                entries=entries.get(row.docket_id, []),
                idb_entries=idb_rows.get(row.docket_id, []),
            )

    def process_row(self, row, header, parties, entries, idb_entries):
        manager = self.index[row.docket_id]
        docket_json = manager.docket_json
        if docket_json:
            search_json = header
            search_json['num_entries'] = len(entries)
            search_json['num_idb_entries'] = len(idb_entries)
            search_json['parties'] = parties
            search_json['entries'] = entries
            search_json['idb_entries'] = idb_entries
            manager.search_json_path.write_text(json.dumps(
                search_json, indent=2, allow_nan=True, default=json_default,
            ))
