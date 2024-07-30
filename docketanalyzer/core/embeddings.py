import faiss
import pandas as pd
from pathlib import Path
import simplejson as json
from toolz import partition_all
from tqdm import tqdm
from docketanalyzer import load_dataset, Chat
from docketanalyzer.utils import DATA_DIR, OPENAI_DEFAULT_EMBEDDING_MODEL, list_to_array


def faiss_search(index, embs, k=1, skips=0, id_map=None, return_ids=False):
    distances, indices = index.search(embs, k + skips)
    results = []
    all_ids = []
    for distance, ids in zip(distances, indices):
        results.append([])
        for i, (d, id) in enumerate(zip(distance, ids)):
            if i >= skips:
                id = id_map[id] if id_map is not None else id
                results[-1].append({
                    'distance': d,
                    'id': id,
                })
                all_ids.append(id)
    if return_ids:
        return results, all_ids
    return results


class EmbeddingSample:
    def __init__(self, embs, id_map=None):
        if isinstance(embs, list):
            embs = list_to_array(embs)
        self.embs = embs
        self.id_map = id_map
        self.index = faiss.IndexFlatL2(embs.shape[1])
        self.index.add(embs)

    def search(self, embs, k=1, skips=0, flat=False):
        results = faiss_search(self.index, embs, k, skips=skips, id_map=self.id_map)
        for i, result in enumerate(results):
            for r in result:
                r['query_idx'] = i
        if flat:
            results = [r for result in results for r in result]
        return results


class Embeddings:
    def __init__(self, path):
        self.path = Path(path)
        try:
            self.config = json.loads(self.config_path.read_text())
        except FileNotFoundError:
            raise FileNotFoundError(f"Embeddings config not found at {self.config_path}. You can try to pull the embeddings first by adding pull=True to load_embeddings.")
        self.dataset = load_dataset(self.config['dataset_name'])
        self.cache = {}
        if self.config['dataset_filter'] is not None:
            self.dataset.set_filter(lambda x: x.filter(**self.config['dataset_filter']))
        self.dataset_col = 'embeddings_added_' + self.config['name']
        if self.dataset_col not in self.dataset.columns:
            self.dataset.add_column(self.dataset_col, 'bool')

    @property
    def config_path(self):
        return self.path / 'config.json'
    
    @property
    def index_path(self):
        return self.path / 'index.faiss'

    @property
    def index(self):
        if 'index' not in self.cache:
            if self.index_path.exists():
                index = faiss.read_index(str(self.index_path))
                index.nprobe = self.config['nprobe']
                self.cache['index'] = index
        return self.cache.get('index')
    
    def save_index(self, index=None):
        if index is None:
            index = self.index
        faiss.write_index(index, str(self.index_path))

    def update(self, reset=False):
        if reset:
            self.dataset.all().update(**{self.dataset_col: False})
        needs_update = self.dataset.exclude(**{self.dataset_col: True})
        chat = Chat(mode='openai')

        for batch in needs_update.batch(100000):
            batch_data = batch.pandas('id', self.config['text_col'])
            texts = batch_data[self.config['text_col']].tolist()
            batch_embeddings = []
            for mini_batch in tqdm(list(partition_all(self.config['batch_size'], texts))):
                batch_embeddings += chat.embed(mini_batch, model=self.config['embedding_model'])
            batch_embeddings = list_to_array(batch_embeddings)
            ids = batch_data['id'].values
            idsel = faiss.IDSelectorArray(ids.size, faiss.swig_ptr(ids))
            self.index.remove_ids(idsel)
            self.index.add_with_ids(batch_embeddings, ids)
            batch.update(**{self.dataset_col: True})
            self.save_index()

    def get_embs(self, ids, return_ids=False):
        if not isinstance(ids, list):
            ids = [ids]
        if not isinstance(ids[0], int):
            pk = self.dataset.pk
            id_map = self.dataset.filter(**{pk + '__in': ids}).values(pk, 'id')
            id_map = {x[pk]: x['id'] for x in id_map}
            ids = [id_map.get(i) for i in ids]
        embs = self.index.reconstruct_batch(ids)
        if return_ids:
            return embs, ids
        return embs
    
    def select(self, ids):
        embs, ids = self.get_embs(ids, return_ids=True)
        data = self.dataset.filter(**{'id__in': ids}).pandas('id', self.dataset.pk, self.config['text_col'])
        return EmbeddingSample(embs, id_map=ids)

    def search(self, embs, k=1, skips=0, flat=False):
        results, all_ids = faiss_search(self.index, embs, k, skips=skips, return_ids=True)
        pk = self.dataset.pk
        text_col = self.config['text_col']
        result_rows = self.dataset.filter(**{'id__in': all_ids}).values('id', pk, text_col)
        result_rows = {x['id']: x for x in result_rows}
        for i, result in enumerate(results):
            for r in result:
                row = result_rows[r['id']]
                r['query_idx'] = i
                r[pk] = row[pk]
                r[text_col] = row[text_col]
        if flat:
            results = [r for result in results for r in result]
        return results

    def push(self, delete=False, exact_timestamps=True):
        from docketanalyzer.cli.sync import sync
        try:
            path = self.path.relative_to(DATA_DIR)
        except ValueError:
            raise ValueError(f"Path {self.path} must be a subpath of {DATA_DIR} to push.")
        sync(path, delete, exact_timestamps, exclude=None, confirm=False, push=True)

    @staticmethod
    def pull(path, delete=False, exact_timestamps=True):
        from docketanalyzer.cli.sync import sync
        try:
            path = path.relative_to(DATA_DIR)
        except ValueError:
            raise ValueError(f"Path {path} must be a subpath of {DATA_DIR} to pull.")
        sync(path, delete, exact_timestamps, exclude=None, confirm=False, push=False)
        
    @staticmethod
    def create(
        name, dataset, text_col, path=None, dataset_filter=None, 
        embedding_model=OPENAI_DEFAULT_EMBEDDING_MODEL, fit_examples=300000,
        nlist=100, m=16, nbits=8, nprobe=10, batch_size=1000
    ):
        if path is None:
            path = DATA_DIR / 'embeddings' / name
        path = Path(path)
        if isinstance(dataset, str):
            dataset = load_dataset(dataset)
        config = {
            'name': name,
            'dataset_name': dataset.name,
            'text_col': text_col,
            'dataset_filter': dataset_filter,
            'embedding_model': embedding_model,
            'fit_examples': fit_examples,
            'nlist': nlist,
            'm': m,
            'nbits': nbits,
            'nprobe': nprobe,
            'batch_size': batch_size,
        }
        path.mkdir(parents=True, exist_ok=True)
        (path / 'config.json').write_text(json.dumps(config, indent=2))

        embeddings = Embeddings(path)
        fit_examples = embeddings.dataset.sample(fit_examples).pandas(dataset.pk, text_col)
        fit_embeddings = []
        chat = Chat(mode='openai')
        for batch in tqdm(list(partition_all(batch_size, fit_examples.to_dict('records')))):
            batch = pd.DataFrame(batch)
            fit_embeddings += chat.embed(batch[text_col].tolist(), model=embedding_model)
        fit_embeddings = list_to_array(fit_embeddings)

        dims = fit_embeddings.shape[1]
        quantizer = faiss.IndexFlatL2(dims)
        index = faiss.IndexIVFPQ(
            quantizer, dims, nlist, m, nbits
        )
        index.train(fit_embeddings)
        index.set_direct_map_type(faiss.DirectMap.Hashtable)
        embeddings.save_index(index)
        embeddings.update()
        return embeddings

    def __len__(self):
        return self.index.ntotal


def load_embeddings(name=None, path=None, pull=False):
    if name is not None:
        path = DATA_DIR / 'embeddings' / name
    path = Path(path)
    if pull:
        Embeddings.pull(path)
    return Embeddings(path)


def create_embeddings(*args, **kwargs):
    return Embeddings.create(*args, **kwargs)
