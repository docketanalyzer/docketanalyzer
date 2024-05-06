import sqlite3
import pandas as pd
from pathlib import Path
import simplejson as json


class CoreDataset:
    def __init__(self, data_dir):
        self.dir = Path(data_dir)
        if not self.dir.exists():
            self.dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.dir / 'dataset.db'
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()

    @property
    def columns(self):
        return self.config['columns']

    @property
    def config_path(self):
        return self.dir / 'config.json'

    @property
    def config(self):
        if not self.config_path.exists():
            self.save_config({})
        return json.loads(self.config_path.read_text())

    def save_config(self, config):
        config['index_col'] = config.get('index_col')
        config['columns'] = config.get('columns')
        self.config_path.write_text(json.dumps(config, indent=2))

    def set_config(self, key, value):
        config = self.config
        config[key] = value
        self.save_config(config)

    def remove_config(self, key):
        config = self.config
        if key in config:
            del config[key]
            self.save_config(config)

    def _initialize_db(self):
        config = self.config
        if self.columns:
            cols = ', '.join([f"{col} TEXT" for col in self.columns])
            self.cursor.execute(f"CREATE TABLE IF NOT EXISTS dataset (idx INTEGER PRIMARY KEY AUTOINCREMENT, {cols})")
            self.conn.commit()

    def add(self, data):
        config = self.config
        if config['index_col']:
            data = data.drop_duplicates(subset=[config['index_col']])
        if self.columns is None:
            self.set_config('columns', [x for x in data.columns if x != 'idx'])
            config = self.config
            self._initialize_db()
        else:
            missing_cols = [x for x in self.columns if x not in data.columns]
            for col in missing_cols:
                data[col] = None
            dropped_cols = [x for x in data.columns if x not in self.columns]
            if dropped_cols:
                print(f"Warning: We are removing the following columns as they are not in the config: {dropped_cols}")
        data = data[self.columns]

        if config['index_col']:
            ids = pd.read_sql_query(f"SELECT {config['index_col']} FROM dataset", self.conn)
            data = data[~data[config['index_col']].isin(ids[config['index_col']])]

        if len(data):
            start_idx = len(self)
            data['idx'] = range(start_idx, start_idx + len(data))
            data.to_sql(name='dataset', con=self.conn, if_exists='append', index=False, dtype={
                'idx': 'INTEGER PRIMARY KEY',
                config['index_col']: 'VARCHAR(128) PRIMARY KEY',
            })
        print(f"Added {len(data)} records to dataset. Total records: {start_idx}")

    def select(self, sample=None, **kwargs):
        query = "SELECT * FROM dataset"
        conditions = []
        values = []  # List to hold the values for the placeholders
        for k, v in kwargs.items():
            parts = k.split('__')
            col_name = parts[0]
            if len(parts) == 1:
                conditions.append(f"{col_name} = ?")
                values.append(v)
            else:
                if parts[1] == 'ne':
                    conditions.append(f"{col_name} != ?")
                    values.append(v)
                elif parts[1] == 'in':
                    conditions.append(f"{col_name} IN ({', '.join(['?' for _ in v])})")
                    values.extend(v)  # Extend the list of values with all values in v
                elif parts[1] == 'nin':
                    conditions.append(f"NOT {col_name} IN ({', '.join(['?' for _ in v])})")
                    values.extend(v)
                elif parts[1] == 'gte':
                    conditions.append(f"{col_name} >= ?")
                    values.append(v)
                elif parts[1] == 'gt':
                    conditions.append(f"{col_name} > ?")
                    values.append(v)
                elif parts[1] == 'lt':
                    conditions.append(f"{col_name} < ?")
                    values.append(v)
                elif parts[1] == 'lte':
                    conditions.append(f"{col_name} <= ?")
                    values.append(v)
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        if sample:
            query += f" ORDER BY RANDOM() LIMIT {sample}"
        data = pd.read_sql_query(query, self.conn, params=values)
        return data.reset_index(drop=True)

    def add_column(self, name, dtype='TEXT', default=None):
        cmd = f"ALTER TABLE dataset ADD COLUMN {name} {dtype}"
        if default:
            cmd += f" DEFAULT {default}"
        self.cursor.execute(cmd)
        self.conn.commit()
        self.set_config('columns', self.columns + [name])

    def delete_column(self, name):
        if name not in self.columns:
            raise ValueError(f"Column {name} does not exist.")
        self.cursor.execute(f"ALTER TABLE dataset DROP COLUMN {name}")
        self.conn.commit()
        self.set_config('columns', [x for x in self.columns if x != name])

    def __len__(self):
        if self.columns:
            self.cursor.execute("SELECT COUNT(*) FROM dataset")
            return self.cursor.fetchone()[0]
        return 0

    def __getitem__(self, key):
        if isinstance(key, int):
            query = f"SELECT * FROM dataset WHERE idx = {key}"
        else:
            query = f"SELECT * FROM dataset WHERE {self.config['index_col']} = '{key}'"
        data = pd.read_sql_query(query, self.conn)
        return data.to_dict('records')[0]


def load_dataset(name):
    from docketanalyzer.utils import DATA_DIR
    return CoreDataset(DATA_DIR / 'datasets' / name)
