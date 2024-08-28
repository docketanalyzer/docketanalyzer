from copy import deepcopy
import numpy as np
import pandas as pd
import simplejson as json
from docketanalyzer import (
    ObjectBatch, extract_attachments, extract_entered_date, mask_text_with_spans, merge_spans
)


class DocketBatch(ObjectBatch):
    @property
    def headers(self):
        if 'headers' not in self.cache:
            choices, values = self.index.choices, self.index.values
            data = []
            for manager in self:
                header = manager.docket_json
                if header:
                    header['docket_id'] = manager.docket_id
                    del header['parties']
                    del header['docket_entries']
                    data.append(header)

            def validate(x, valid_items):
                if x not in valid_items:
                    raise ValueError(f"Invalid value '{x}'.")

            data = pd.DataFrame(data)
            data = data.drop(columns=['ordered_by'])
            data = data.rename(columns={
                'court_id': 'court', 
                'nature_of_suit': 'nature_suit',
                'assigned_to_str': 'assigned_judge',
                'referred_to_str': 'referred_judge',
            })

            data['court'].apply(lambda x: validate(x, choices['DistrictCourt']))
            data['case_type'] = data['docket_number'].apply(lambda x: x.split('-')[1])
            data['case_type'] = data['case_type'].apply(lambda x: x if x in choices['CaseType'] else 'other')
            data['nature_suit'] = data['nature_suit'].apply(lambda x: None if not x else '_' + x.split()[0].strip())
            data['nature_suit'].apply(lambda x: None if pd.isnull(x) else validate(x, choices['NatureSuit']))
            data['jury_demand'] = data['jury_demand'].apply(lambda x: None if not x else values['JuryDemand'][x])
            data['jurisdiction'] = data['jurisdiction'].apply(lambda x: None if not x else values['Jurisdiction'][x])
            data['date_filed'] = pd.to_datetime(data['date_filed'], errors='coerce')
            data['date_terminated'] = pd.to_datetime(data['date_terminated'], errors='coerce')
            self.cache['headers'] = data
        return self.cache['headers']
    
    @property
    def header(self):
        return self.headers

    @property
    def parties_and_counsel(self):
        if 'parties' not in self.cache or 'counsel' not in self.cache:
            parties, counsel = [], []
            for manager in self:
                docket_json = manager.docket_json
                if docket_json:
                    for i, party in enumerate(docket_json['parties']):
                        party_counsel = party.pop('attorneys', [])
                        party_id = f"{manager.docket_id}__{i}"
                        parties.append({
                            'docket_id': manager.docket_id,
                            'party_row': i,
                            'party_id': party_id,
                            **party
                        })
                        for j, attorney in enumerate(party_counsel):
                            counsel.append({
                                'docket_id': manager.docket_id,
                                'party_id': party_id,
                                'attorney_row': j,
                                'attorney_id': f"{manager.docket_id}__{i}__{j}",
                                **attorney
                            })

            parties = pd.DataFrame(parties)
            parties['type'] = parties['type'].apply(lambda x: self.index.values['PartyType'].get(x, 'other'))
            parties['date_terminated'] = pd.to_datetime(parties['date_terminated'], errors='coerce')
            if 'criminal_data' not in parties.columns:
                parties['criminal_data'] = None
            parties.loc[parties['criminal_data'].notnull(), 'criminal_data'] = (
                parties[parties['criminal_data'].notnull()]['criminal_data'].apply(json.dumps)
            )

            counsel = pd.DataFrame(counsel)
            counsel['roles'] = counsel['roles'].apply(json.dumps)
            self.cache['parties'] = parties
            self.cache['counsel'] = counsel
        return self.cache['parties'], self.cache['counsel']

    @property
    def parties(self):
        return self.parties_and_counsel[0]

    @property
    def counsel(self):
        return self.parties_and_counsel[1]

    def get_entries(self, include_spans=True, process_text=True, add_shuffle_number=False):
        data = []
        for manager in self:
            docket_json = manager.docket_json
            if docket_json:
                entries = pd.DataFrame(docket_json['docket_entries'])
                if len(entries):
                    entries['docket_id'] = manager.docket_id
                    entries['row_number'] = range(len(entries))
                    if add_shuffle_number:
                        entries['shuffle_number'] = np.random.permutation(len(entries))
                    data.append(entries)
        if not len(data):
            return None
        data = pd.concat(data)
        data = data.rename(columns={'document_number': 'entry_number'})
        data['description'] = data['description'].apply(lambda x: x if pd.isnull(x) else x[:20000])
        data['entry_id'] = data.apply(lambda x: f"{x['docket_id']}__{x['row_number']}", axis=1)
        data['date_filed'] = pd.to_datetime(data['date_filed'], errors='coerce')
        data['pacer_doc_id'] = data['pacer_doc_id'].astype(pd.Int64Dtype())
        data['entry_number'] = data['entry_number'].astype(pd.Int64Dtype())
        data['pacer_seq_no'] = data['pacer_seq_no'].astype(pd.Int64Dtype())
        data['date_entered'] = pd.to_datetime(data['date_entered'], errors='coerce')

        if include_spans:
            spans = self.entry_spans
            spans = spans.drop(columns=['docket_id', 'row_number'])
            spans = spans.groupby('entry_id').apply(lambda x: x.to_dict(orient='records')).reset_index()
            spans.columns = ['entry_id', 'spans']
            data = data.merge(spans, on='entry_id', how='left')

        if process_text:
            def consolidate_spans(spans, attachments, entered_date):
                spans = spans if isinstance(spans, list) else []
                spans += entered_date
                attachment_items = []
                for attachment in deepcopy(attachments):
                    for attachment_item in attachment.pop('attachments'):
                        attachment_items.append({
                            'label': 'attachment',
                            'start': attachment_item['start'],
                            'end': attachment_item['end'],
                        })
                spans += attachments + attachment_items
                return spans

            def make_simple_text(text, attachments, entered_date):
                text = mask_text_with_spans(
                    text, merge_spans(attachments + entered_date),
                    mapper=lambda _, span: ' '
                )
                text = ' '.join(text.split())
                return text

            def make_masked_text(text, spans):
                return mask_text_with_spans(
                    text, merge_spans([x for x in spans if x['label'] not in ['detail', 'attachment']]),
                    mapper=lambda _, span: f"<{span['label']} {span['start']}>"
                )

            data['attachments'] = data['description'].apply(extract_attachments)
            data['entered_date'] = data['description'].apply(extract_entered_date)
            if 'spans' not in data.columns:
                data['spans'] = None
            data['spans'] = data.apply(lambda x: consolidate_spans(x['spans'], x['attachments'], x['entered_date']), axis=1)
            data['simple_text'] = data.apply(lambda x: make_simple_text(x['description'], x['attachments'], x['entered_date']), axis=1)
            data['masked_text'] = data.apply(lambda x: make_masked_text(x['description'], x['spans']), axis=1)
        return data

    @property
    def entry_spans(self):
        if 'entry_spans' not in self.cache:
            data = []
            for manager in self:
                for path in manager.span_paths:
                    span_data = pd.read_csv(path)
                    span_data['docket_id'] = manager.docket_id
                    span_data['row_number'] = span_data['row_number'].astype(int)
                    span_data['entry_id'] = span_data.apply(lambda x: f"{x['docket_id']}__{x['row_number']}", axis=1)
                    data.append(span_data)
            if not len(data):
                data = None
            else:
                data = pd.concat(data)
            self.cache['entry_spans'] = data
        return self.cache['entry_spans']
                    
    @property
    def entries(self):
        if 'entries' not in self.cache:
            self.cache['entries'] = self.get_entries()
        return self.cache['entries']

    @property
    def docs(self):
        data = []
        for manager in self:
            for doc in manager.all_docs:
                data.append({
                    'docket_id': manager.docket_id,
                    'entry_number': doc.entry_number,
                    'attachment_number': doc.attachment_number,
                    'name': doc.name,
                    'pdf_available': doc.pdf_available,
                    'ocr_available': doc.ocr_available,
                })
        if not len(data):
            return None
        data = pd.DataFrame(data)
        if len(data):
            data['doc_id'] = data.apply(lambda x: f"{x['docket_id']}__{x['name']}", axis=1)
            data['entry_number'] = data['entry_number'].astype(pd.Int64Dtype())
            data['attachment_number'] = data['attachment_number'].astype(pd.Int64Dtype())
            return data

    def clear_cache(self):
        self.cache = {}
