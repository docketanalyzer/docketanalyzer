import simplejson as json
from docketanalyzer import choices
from .task import DocketTask


class ConsolidateSearchDocket(DocketTask):
    """
    Consolidate search docket.
    """
    name = 'consolidate-search'
    batch_size = 5000
    workers = None
    depends_on = ['parse-dockets', 'find-idb-entries']
    inactive = False

    def prepare(self):
        self.court_choices = {x[0]: x[1] for x in choices.DistrictCourt.choices()}
        self.case_type_choices = {x[0]: x[1] for x in choices.CaseType.choices()}
        self.nature_suit_choices = {x[0]: x[1] for x in choices.NatureSuit.choices()}
        self.jury_demand_choices_swapped = {x[1]: x[0] for x in choices.JuryDemand.choices()}
        self.jurisdiction_choices_swapped = {x[1]: x[0] for x in choices.Jurisdiction.choices()}

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

        entries = docket_batch.entries.groupby('docket_id').apply(lambda x:
            x.to_dict('records')
        , include_groups=False).to_dict()
  
        parties, counsel = docket_batch.parties_and_counsel
        counsel = counsel.drop(columns=['docket_id'])
        counsel = counsel.groupby('party_id').apply(lambda x:
            x.to_dict('records')
        , include_groups=False).to_dict()
        parties['counsel'] = parties['party_id'].apply(lambda x:
            counsel.get(x, [])
        )
        parties = parties.groupby('docket_id').apply(lambda x:
            x.to_dict('records')
        , include_groups=False).to_dict()

        for row in batch:
            self.process_row(row,
                parties.get(row.docket_id, []),
                entries=entries.get(row.docket_id, []),
                idb_entries=idb_rows.get(row.docket_id, []),
            )

    def process_row(self, row, parties, entries, idb_entries):
        manager = self.index[row.docket_id]
        docket_json = manager.docket_json
        if docket_json:
            court_id = docket_json['court_id']
            if court_id not in self.court_choices:
                raise ValueError(f"Invalid court_id: {court_id}")
                court_id = None

            docket_number = docket_json['docket_number']

            case_type = docket_number.split('-')[1]
            if case_type not in self.case_type_choices:
                print(f"Invalid case_type: {case_type}")

            nature_suit = docket_json.get('nature_of_suit')
            if nature_suit:
                nature_suit = '_' + nature_suit.split()[0]
                if nature_suit not in self.nature_suit_choices:
                    raise ValueError(f"Invalid nature_suit: {nature_suit}")
                    nature_suit = None

            jury_demand = docket_json.get('jury_demand')
            if jury_demand:
                if jury_demand not in self.jury_demand_choices_swapped:
                    raise ValueError(f"Invalid jury_demand: {jury_demand}")
                    jury_demand = None
                jury_demand = self.jury_demand_choices_swapped[jury_demand]

            jurisdiction = docket_json.get('jurisdiction')
            if jurisdiction:
                if jurisdiction not in self.jurisdiction_choices_swapped:
                    raise ValueError(f"Invalid jurisdiction: {jurisdiction}")
                    jurisdiction = None
                jurisdiction = self.jurisdiction_choices_swapped[jurisdiction]

            search_json = {
                'docket_id': row.docket_id,
                'court_id': court_id,
                'case_type': case_type,
                'docket_number': docket_number,
                'nature_of_suit': nature_suit,
                'date_filed': docket_json['date_filed'],
                'date_terminated': docket_json['date_terminated'],
                'cause': docket_json['cause'],
                'case_name': docket_json['case_name'],
                'jury_demand': jury_demand,
                'jurisdiction': jurisdiction,
                'num_entries': len(entries),
                'num_idb_entries': len(idb_entries),
                'parties': parties,
                'entries': entries,
                'idb_entries': idb_entries,
            }
            manager.search_json_path.write_text(json.dumps(search_json, indent=2, default=str))
