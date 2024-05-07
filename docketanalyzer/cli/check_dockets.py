from datetime import datetime
import click
import pandas as pd
from toolz import partition_all
from tqdm import tqdm
from docketanalyzer import DocketManager, load_dataset
from docketanalyzer.utils import DATA_DIR


@click.command()
def check_dockets():
    """
    Checks and updates the core dataset for indexing all dockets in the DA_DATA_DIR.
    """
    dataset = load_dataset('dockets')
    dataset.set_config('index_col', 'docket_id')

    dockets_dir = DATA_DIR / 'dockets' / 'data'
    dockets_dir.mkdir(parents=True, exist_ok=True)
    docket_ids = pd.DataFrame({'docket_id':
        [x.name for x in dockets_dir.iterdir()]
    })

    if len(docket_ids):
        batch_size = 100000
        for batch in tqdm(list(partition_all(batch_size, docket_ids.to_dict('records')))):
            dataset.add(pd.DataFrame(batch))
    dataset.set_config('last_update', str(datetime.now()))
