import click
from docketanalyzer import CoreDataset
from docketanalyzer.utils import DATA_DIR


@click.command()
def prepare_idb_dataset():
    idb_data_dir = DATA_DIR / 'datasets' / 'idb'
    idb_data_dir.mkdir(parents=True, exist_ok=True)
    raw_data_path = idb_data_dir / 'raw.csv'
    print(DATA_DIR)
    print(CoreDataset)
