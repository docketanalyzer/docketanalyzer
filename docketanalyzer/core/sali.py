import pandas as pd
from pathlib import Path
from docketanalyzer import demo_data_path


class SALI:
    def __init__(self):
        self.cache = {}

    @property
    def raw_data(self):
        if 'raw_data' not in self.cache:
            self.cache['raw_data'] = pd.read_csv(demo_data_path('sali.csv'))
        return self.cache['raw_data']

    @property
    def data(self):
        if 'data' not in self.cache:
            data = self.raw_data
            data['name'] = data['http://www.w3.org/2000/01/rdf-schema#label'].apply(lambda x: x if pd.isnull(x) else x[1:-1])
            data['definition'] = data['http://www.w3.org/2004/02/skos/core#definition'].apply(lambda x: x if pd.isnull(x) else x[1:-1])
            data['defined_by'] = data['http://www.w3.org/2000/01/rdf-schema#isDefinedBy'].apply(lambda x: x if pd.isnull(x) else x[1:-1])
            ent2name = {x['Entity']: x['name'] for x in data.to_dict('records')}
            data['parents'] = data['Superclass(es)'].apply(lambda x: [] if pd.isnull(x) else [ent2name[y] for y in x.split('\t')])
            data = data[['name', 'parents', 'definition', 'defined_by']].dropna(subset='name')
            self.cache['data'] = data
        return self.cache['data']
    
    @property
    def name2parents(self):
        if 'name2parents' not in self.cache:
            data = self.data
            data = {x['name']: x['parents'] for x in data.to_dict('records')}
            self.cache['name2parents'] = data
        return self.cache['name2parents']

    @property
    def name2children(self):
        if 'name2children' not in self.cache:
            data = self.data
            data = data.explode('parents')
            data = data.groupby('parents').apply(lambda x: x['name'].tolist()).reset_index()
            data.columns = ['name', 'children']
            data = {x['name']: x['children'] for x in data.to_dict('records')}
            self.cache['name2children'] = data
        return self.cache['name2children']

    def get_tree(self, name, mapper, passed=[]):
        tree = {}
        related = mapper.get(name, [])
        related = [x for x in related if x not in passed]
        passed = list(set(passed + related + [name]))
        for relation in related:
            tree[relation] = self.get_tree(relation, mapper, passed=passed)
        return tree
    
    def get_descendants(self, name):
        return self.get_tree(name, self.name2children)
    
    def get_ancestors(self, name):
        return self.get_tree(name, self.name2parents)
    
    def get_keys(self, x):
        keys = set(x.keys())
        for k, v in x.items():
            keys.update(self.get_keys(v))
        return list(keys)
