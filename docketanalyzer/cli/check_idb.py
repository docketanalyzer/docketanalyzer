from datetime import datetime
from bs4 import BeautifulSoup
import click
import pandas as pd
import regex as re
import requests
from tqdm import tqdm
import wget
import zipfile
from docketanalyzer import load_dataset
from docketanalyzer.choices import (
    IDBArbitrationAtFiling,
    IDBArbitrationAtTermination,
    IDBClassAction,
    IDBDisposition,
    IDBIFP,
    IDBJudgment,
    IDBMDL,
    IDBNatureOfJudgment,
    IDBOrigin,
    IDBProceduralProgress,
    IDBProSe,
    IDBStatusCode,
)
from docketanalyzer.utils import DATA_DIR, notabs
pd.options.mode.chained_assignment = None


local_dir = DATA_DIR / 'local'

fjc_district_codes = {"00": "med", "47": "ohnd", "01": "mad", "48": "ohsd", "02": "nhd", "49": "tned", "03": "rid", "50": "tnmd", "04": "prd", "51": "tnwd", "05": "ctd", "52": "ilnd", "06": "nynd", "53": "ilcd", "07": "nyed", "54": "ilsd", "08": "nysd", "55": "innd", "09": "nywd", "56": "insd", "10": "vtd", "57": "wied", "11": "ded", "58": "wiwd", "12": "njd", "60": "ared", "13": "paed", "61": "arwd", "14": "pamd", "62": "iand", "15": "pawd", "63": "iasd", "16": "mdd", "64": "mnd", "17": "nced", "65": "moed", "18": "ncmd", "66": "mowd", "19": "ncwd", "67": "ned", "20": "scd", "68": "ndd", "22": "vaed", "69": "sdd", "23": "vawd", "7-": "akd", "24": "wvnd", "70": "azd", "25": "wvsd", "71": "cand", "26": "alnd", "72": "caed", "27": "almd", "73": "cacd", "28": "alsd", "74": "casd", "29": "flnd", "75": "hid", "3A": "flmd", "76": "idd", "3C": "flsd", "77": "mtd", "3E": "gand", "78": "nvd", "3G": "gamd", "79": "ord", "3J": "gasd", "80": "waed", "3L": "laed", "81": "wawd", "3N": "lamd", "82": "cod", "36": "lawd", "83": "ksd", "37": "msnd", "84": "nmd", "38": "mssd", "85": "oknd", "39": "txnd", "86": "oked", "40": "txed", "87": "okwd", "41": "txsd", "88": "utd", "42": "txwd", "89": "wyd", "43": "kyed", "90": "dcd", "44": "kywd", "91": "vid", "45": "mied", "93": "gud", "46": "miwd", "94": "nmid"}


fields = {
    'origin': {
        'col': 'ORIGIN',
        'cat': IDBOrigin,
        'mapping': {
            '1': 'Original Proceeding',
            '2': 'Removed',
            '3': 'Remanded for Further Action',
            '4': 'Reinstated/Reopened',
            '5': 'Transferred from Another District',
            '6': 'Multi District Litigation',
            '7': 'Appeal to District Judge of Magistrate Judge Decision',
            '8': 'Second Reopen',
            '9': 'Third Reopen',
            '10': 'Fourth Reopen',
            '11': 'Fifth Reopen',
            '12': 'Sixth Reopen',
            '13': 'Multi District Litigation Originating in the District',
        },
    },

    'procedural_progress': {
        'col': 'PROCPROG',
        'cat': IDBProceduralProgress,
        'mapping': {
            '1': 'Before Issue Joined - No Court Action',
            '2': 'Before Issue Joined - Order Entered',
            '11': 'Before Issue Joined - Hearing Held',
            '12': 'Before Issue Joined - Order Decided',
            '3': 'After Issue Joined - No Court Action',
            '4': 'After Issue Joined - Judgment on Motion',
            '5': 'After Issue Joined - Pretrial Conference Held',
            '6': 'After Issue Joined - During Court Trial',
            '7': 'After Issue Joined - During Jury Trial',
            '8': 'After Issue Joined - After Court Trial',
            '9': 'After Issue Joined - After Jury Trial',
            '10': 'After Issue Joined - Other',
            '13': 'After Issue Joined - Request for Trial De Novo After Arbitration',
            '-8': 'Missing',
        },
    },

    'disposition': {
        'col': 'DISP',
        'cat': IDBDisposition,
        'mapping': {
            '0': 'Transfer to Another District',
            '1': 'Remanded to State Court',
            '10': 'Multi District Litigation Transfer',
            '11': 'Remanded to U.S. Agency',
            '2': 'Dismissal - Want of Prosecution',
            '3': 'Dismissal - Lack of Jurisdiction',
            '12': 'Dismissal - Voluntarily',
            '13': 'Dismissal - Settled',
            '14': 'Dismissal - Other',
            '4': 'Judgment on Default',
            '5': 'Judgment on Consent',
            '6': 'Judgment on Motion Before Trial',
            '7': 'Judgment on Jury Verdict',
            '8': 'Judgment on Directed Verdict',
            '9': 'Judgment on Court Trial',
            '15': 'Judgment on Award of Arbitrator',
            '16': 'Stayed Pending Bankruptcy',
            '17': 'Other',
            '18': 'Statistical Closing',
            '19': 'Appeal Affirmed (Magistrate Judge)',
            '20': 'Appeal Denied (Magistrate Judge)',
            '-8': 'Missing',
        },
    },

    'pro_se': {
        'col': 'PROSE',
        'cat': IDBProSe,
        'mapping': {
            '0': 'None',
            '1': 'Plaintiff',
            '2': 'Defendant',
            '3': 'Both Plaintiff & Defendant',
            '-8': 'Missing',
        },
    },

    'judgment': {
        'col': 'JUDGMENT',
        'cat': IDBJudgment,
        'mapping': {
            '1': 'Plaintiff',
            '2': 'Defendant',
            '3': 'Both',
            '4': 'Unknown',
            '0': 'Missing',
            '-8': 'Missing',
        },
    },

    'nature_of_judgment': {
        'col': 'NOJ',
        'cat': IDBNatureOfJudgment,
        'mapping': {
            '0': 'No Monetary Award',
            '1': 'Monetary Award Only',
            '2': 'Monetary Award and Other',
            '3': 'Injunction',
            '4': 'Forfeiture/Foreclosure/Condemnation, etc.',
            '5': 'Costs Only',
            '6': 'Costs and Attorney Fees',
            '-8': 'Missing',
        },
    },

    'status_code': {
        'col': 'STATUSCD',
        'cat': IDBStatusCode,
        'mapping': {
            'S': 'Pending Record',
            'L': 'Terminated Record',
            'nan': 'Missing',
            'None': 'Missing',
        },
    },

    'arbitration_at_filing': {
        'col': 'ARBIT',
        'cat': IDBArbitrationAtFiling,
        'mapping': {
            'M': 'Mandatory',
            'V': 'Voluntary',
            'E': 'Exempt',
            'Y': 'Yes, Type Unknown',
            'N': 'No',
            '-8': 'Missing',
        },
    },

    'arbitration_at_termination': {
        'col': 'TRMARB',
        'cat': IDBArbitrationAtTermination,
        'mapping': {
            'M': 'Mandatory',
            'V': 'Voluntary',
            'E': 'Exempt',
            '-8': 'Missing',
        },
    },
}


def get_last_idb_update():
    url = 'https://www.fjc.gov/research/idb/civil-cases-filed-terminated-and-pending-sy-1988-present'
    r = requests.get(url)
    soup = BeautifulSoup(r.content, 'html.parser')

    last_idb_update = soup.find(class_='views-field-field-description')
    last_idb_update = re.search(
        r'pending as of (\w+ \d{1,2}, \d{4})', 
        last_idb_update.text,
    ).group(1)
    return pd.to_datetime(last_idb_update).date()


def download_idb_data(dataset):
    print('\nDownloading the latest IDB data...')
    url = 'https://www.fjc.gov/sites/default/files/idb/textfiles/cv88on.zip'
    download_path = local_dir / 'raw.zip'
    wget.download(url, out=str(download_path))
    print('\nExtracting the data...')
    with zipfile.ZipFile(download_path, 'r') as f:
        f.extractall(local_dir)
    path = local_dir / 'cv88on.txt'
    path.rename(local_dir / 'idb_raw.txt')
    download_path.unlink()
    dataset.config['last_download_date'] = str(datetime.now())
    print(f"\nDownload complete! The raw data is located at: {local_dir / 'idb_raw.txt'}")


def load_raw_idb_data(dataset, **kwargs):
    return pd.read_csv(
        local_dir / 'idb_raw.txt',
        sep='\t', encoding='ISO-8859-1',
        dtype={'DOCKET': str, 'OFFICE': str, 'DISTRICT': str},
        **kwargs
    )


def process_chunk(chunk, start_row=0):
    chunk['idb_row'] = range(start_row, start_row + len(chunk))
    chunk['idb_row'] = '_' + chunk['idb_row'].astype(str)
    data = chunk[['idb_row']]
    data['court'] = chunk['DISTRICT'].apply(lambda x: fjc_district_codes[x.zfill(2)])
    data['filing_date'] = pd.to_datetime(chunk['FILEDATE']).dt.date
    data['terminating_date'] = pd.to_datetime(chunk['TERMDATE']).dt.date
    data['ifp'] = chunk['IFP'].apply(lambda x: IDBIFP('Yes' if str(x) != '-8' else 'No').name)
    data['mdl'] = chunk['MDLDOCK'].apply(lambda x: IDBMDL('Yes' if str(x) != '-8' else 'No').name)
    data['class_action'] = chunk['CLASSACT'].apply(lambda x:  IDBClassAction('Yes' if str(x) != '-8' else 'No').name)
    for field_name, field in fields.items():
        data[field_name] = chunk[field['col']].apply(lambda x:
            None if pd.isnull(x) or str(x) not in field['mapping'] else
            field['cat'](field['mapping'][str(x)]).name
        )
    data['docket_id'] = (
        data['court'] + '__' +
        chunk['OFFICE'] + '_' + chunk['DOCKET'].apply(lambda x: x[:-5]) +
        '-cv-' + chunk['DOCKET'].apply(lambda x: x[-5:])
    ).str.lower()
    data['alternate_id'] = (
        data['court'] + '_' +
        data['docket_id'].apply(lambda x: x.split(':')[-1]) + '_' + data['filing_date'].astype(str)
    )
    return data


def check_idb(reset=False, quiet=True, local=False, skip_row_check=False):
    """
    Downloads and prepares a core dataset with datafrom the IDB. We check the IDB for new data and update the dataset if necessary.
    """
    print('\n\n\n\n' + notabs("""

    RUNNING IDB CHECKER

    We will:
    - Download or update the raw IDB data
    - Convert the data to a CoreDataset format
    """))

    dataset = load_dataset('idb', pk='idb_row', local=local)
    if reset:
        dataset.delete(quiet=True)
        dataset = load_dataset('idb', pk='idb_row', local=local)

    has_new_data = False
    local_path = local_dir / 'idb_raw.txt'
    local_dir.mkdir(parents=True, exist_ok=True)
    last_download_date = dataset.config.get('last_download_date')
    if last_download_date is None or not local_path.exists():
        has_new_data = True
        print("\n\nIt looks like this is the first time you're running the IDB checker.")
        download_idb_data(dataset)
    last_download_date = pd.to_datetime(dataset.config['last_download_date']).date()

    last_idb_update = get_last_idb_update()
    print(f"\n\nIDB last update: {last_idb_update}")
    print(f"Last download: {last_download_date}")
    if last_download_date >= last_idb_update:
        print("\nYour IDB data is up to date!")
    else:
        print(f"\n\nIt looks like your IDB dataset is out of date.\nWould you like to update it?")
        if quiet or click.confirm('\nRun updates?'):
            if local_path.exists():
                local_path.unlink()
            dataset.delete(quiet=True)
            dataset = load_dataset('idb', pk='idb_row', local=local)
            download_idb_data(dataset)
            has_new_data = True
        else:
            print("Ok, we will continue with the existing data.")

    if skip_row_check and not has_new_data:
        print('\n\nSkipping core dataset check as there are no new updates.')
    else:
        print('\n\nChecking core dataset...')
        total_records = len(load_raw_idb_data(dataset))
        dataset_records = len(dataset)
        print(f"\nRaw IDB records: {total_records}")
        print(f"Core dataset records: {dataset_records}")
        if total_records > dataset_records:
            print(f"\n{total_records - dataset_records} records need to be added to the core dataset.")
            chunksize = 200000
            chunks = load_raw_idb_data(
                dataset,
                chunksize=chunksize,
                low_memory=False,
                skiprows=range(1, dataset_records + 1),
            )
            start_row = dataset_records
            print("Adding data...")
            for chunk in tqdm(chunks, total=(total_records - dataset_records) // chunksize):
                chunk = process_chunk(chunk, start_row=start_row)
                dataset.add(chunk, verbose=False)
                start_row += len(chunk)

    print(f"\n\nIDB check complete!\n\nUse load_dataset('idb') to load the dataset in your code.")


@click.command('check-idb')
@click.option('--reset', is_flag=True, help="Scrap any existing data and start fresh.")
@click.option('--quiet', '-q', is_flag=True, help="Automatically accepts all prompts.")
@click.option('--local', '-l', is_flag=True, help="Force the use of local core dataset.")
def check_idb_command(reset, quiet, local):
    check_idb(reset, quiet, local)
