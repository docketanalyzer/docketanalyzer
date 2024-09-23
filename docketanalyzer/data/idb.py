from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime
import math
from bs4 import BeautifulSoup
from pathlib import Path
import pandas as pd
import regex as re
import requests
import simplejson as json
from tqdm import tqdm
import zipfile
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
from docketanalyzer import (
    DATA_DIR, notabs, connect, download_file,
    require_confirmation_wrapper, json_default,
    pd_save_or_append, cpu_workers
)

pd.options.mode.chained_assignment = None


IDB_UPDATES_URL = 'https://www.fjc.gov/research/idb/civil-cases-filed-terminated-and-pending-sy-1988-present'

IDB_DOWNLOAD_URL = 'https://www.fjc.gov/sites/default/files/idb/textfiles/cv88on.zip'

IDB_FILE_NAME = 'cv88on.txt'

FJC_DISTRICT_CODES = {"00": "med", "47": "ohnd", "01": "mad", "48": "ohsd", "02": "nhd", "49": "tned", "03": "rid", "50": "tnmd", "04": "prd", "51": "tnwd", "05": "ctd", "52": "ilnd", "06": "nynd", "53": "ilcd", "07": "nyed", "54": "ilsd", "08": "nysd", "55": "innd", "09": "nywd", "56": "insd", "10": "vtd", "57": "wied", "11": "ded", "58": "wiwd", "12": "njd", "60": "ared", "13": "paed", "61": "arwd", "14": "pamd", "62": "iand", "15": "pawd", "63": "iasd", "16": "mdd", "64": "mnd", "17": "nced", "65": "moed", "18": "ncmd", "66": "mowd", "19": "ncwd", "67": "ned", "20": "scd", "68": "ndd", "22": "vaed", "69": "sdd", "23": "vawd", "7-": "akd", "24": "wvnd", "70": "azd", "25": "wvsd", "71": "cand", "26": "alnd", "72": "caed", "27": "almd", "73": "cacd", "28": "alsd", "74": "casd", "29": "flnd", "75": "hid", "3A": "flmd", "76": "idd", "3C": "flsd", "77": "mtd", "3E": "gand", "78": "nvd", "3G": "gamd", "79": "ord", "3J": "gasd", "80": "waed", "3L": "laed", "81": "wawd", "3N": "lamd", "82": "cod", "36": "lawd", "83": "ksd", "37": "msnd", "84": "nmd", "38": "mssd", "85": "oknd", "39": "txnd", "86": "oked", "40": "txed", "87": "okwd", "41": "txsd", "88": "utd", "42": "txwd", "89": "wyd", "43": "kyed", "90": "dcd", "44": "kywd", "91": "vid", "45": "mied", "93": "gud", "46": "miwd", "94": "nmid"}

IDB_FIELDS = {
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


def process_chunk(idb_dir, chunk, start_row=0):
    chunk = IDB.process_chunk(chunk, start_row=start_row)
    out_path = idb_dir / f'chunk.{start_row}.csv'
    chunk.to_csv(out_path, index=False)


class IDB:
    DATE_COLUMNS = [
        'filing_date', 'terminating_date', 'fdateuse_raw', 
        'transdat_raw', 'tdateuse_raw', 'djoined_raw', 
        'pretrial_raw', 'tribegan_raw', 'trialend_raw',
    ]

    def __init__(self, skip_db=False):
        self.dir = DATA_DIR / 'data' / 'idb'
        self.data_path = self.dir / 'data.csv'
        self.raw_data_path = self.dir / 'raw.zip'
        self.extracted_data_path = self.dir / IDB_FILE_NAME
        self.status_path = self.dir / 'status.json'
        self.db = None
        if not skip_db:
            self.db = connect()
        self.cache = {}

    @property
    def last_update(self):
        if 'last_update' not in self.cache:
            r = requests.get(IDB_UPDATES_URL)
            soup = BeautifulSoup(r.content, 'html.parser')
            last_idb_update = soup.find(class_='views-field-field-description')
            last_idb_update = re.search(
                r'pending as of (\w+ \d{1,2}, \d{4})', 
                last_idb_update.text,
            ).group(1)
            self.cache['last_update'] = pd.to_datetime(last_idb_update).date()
        return self.cache['last_update']

    @property
    def status(self):
        status = {}
        if self.status_path.exists():
            status = json.loads(self.status_path.read_text())
        if status.get('last_download_date') is not None:
            status['last_download_date'] = pd.to_datetime(status['last_download_date']).date()
        status['db_needs_reset'] = status.get('db_needs_reset', True)
        return status
    
    def save_status(self, key, value):
        status = self.status
        status[key] = value
        self.status_path.write_text(json.dumps(status, default=json_default))

    def reset_status(self):
        if self.status_path.exists():
            self.status_path.unlink()

    def download_raw_data(self):
        if self.raw_data_path.exists():
            self.raw_data_path.unlink()
        if self.extracted_data_path.exists():
            self.extracted_data_path.unlink()
        self.reset_status()
        download_file(IDB_DOWNLOAD_URL, self.raw_data_path, description='Downloading IDB data')
        print('Extracting downloaded contents.')
        with zipfile.ZipFile(self.raw_data_path, 'r') as f:
            f.extractall(self.dir)
        print('Cleaning up.')
        self.raw_data_path.unlink()
        self.save_status('last_download_date', str(datetime.now()))

    def load_raw_data(self, low_memory=False, **kwargs):
        return pd.read_csv(
            self.extracted_data_path,
            sep='\t', encoding='ISO-8859-1',
            dtype={'DOCKET': str, 'OFFICE': str, 'DISTRICT': str},
            low_memory=low_memory, **kwargs
        )

    @staticmethod
    def process_chunk(chunk, start_row=0):
        chunk['idb_row'] = range(start_row, start_row + len(chunk))
        chunk['idb_row'] = '_' + chunk['idb_row'].astype(str)
        data = chunk[['idb_row']]
        data['court'] = chunk['DISTRICT'].apply(lambda x: FJC_DISTRICT_CODES[x.zfill(2)])
        data['filing_date'] = pd.to_datetime(chunk['FILEDATE']).dt.date
        data['terminating_date'] = pd.to_datetime(chunk['TERMDATE']).dt.date
        data['ifp'] = chunk['IFP'].apply(lambda x: IDBIFP('Yes' if str(x) != '-8' else 'No').value)
        data['mdl'] = chunk['MDLDOCK'].apply(lambda x: IDBMDL('Yes' if str(x) != '-8' else 'No').value)
        data['class_action'] = chunk['CLASSACT'].apply(lambda x:  IDBClassAction('Yes' if str(x) != '-8' else 'No').value)
        for field_name, field in IDB_FIELDS.items():
            data[field_name] = chunk[field['col']].apply(lambda x:
                None if pd.isnull(x) or str(x) not in field['mapping'] else
                field['cat'](field['mapping'][str(x)]).value
            )
        for col in [
            'CIRCUIT', 'AMTREC', 'FDATEUSE', 'JURIS', 'TITL', 'SECTION', 'SUBSECT', 'RESIDENC', 
            'JURY', 'DEMANDED', 'FILEJUDG', 'FILEMAG', 'COUNTY', 'PLT', 'DEF', 
            'TRANSDAT', 'TRANSOFF', 'TRANSDOC', 'TRANSORG', 'TDATEUSE', 'TRCLACT', 'TERMJUDG', 'TERMMAG',
            'DJOINED', 'PRETRIAL', 'TRIBEGAN', 'TRIALEND', 'TAPEYEAR',
        ]:
            data[col.lower() + '_raw'] = chunk[col]
        data['docket_id'] = (
            data['court'] + '__' +
            chunk['OFFICE'] + '_' + chunk['DOCKET'].apply(lambda x: x[:-5]) +
            '-cv-' + chunk['DOCKET'].apply(lambda x: x[-5:])
        ).str.lower()
        data['alternate_id'] = (
            data['court'] + '__' +
            data['docket_id'].apply(lambda x: x.split('_')[-1]) + '__' + data['filing_date'].astype(str)
        )
        return data

    def infer_dtypes(self):
        data = pd.read_csv(self.data_path, nrows=500000, low_memory=False)
        dtype_map = {}
        for col in data.columns:
            dtype = data[col].dtype
            if col in self.DATE_COLUMNS:
                dtype_map[col] = 'DateField'
            elif dtype in ['float64', 'object', 'int64']:
                dtype_map[col] = 'CharField'
            else:
                raise ValueError(f"Unknown dtype for column {col}: {dtype}")
        return dtype_map
    
    @require_confirmation_wrapper(
        message=lambda args: notabs(f"""
            Are you sure you want to reset your IDB data?
            This will DELETE ANY LOCAL DATA and DROP THE DATABASE TABLE.
        """),
        disable=lambda args: not args.get('confirm', True),
    )
    def reset(self, confirm=True):
        self.reset_status()
        if self.data_path.exists():
            self.data_path.unlink()
        if self.db is not None:
            if 'idb' in self.db.t:
                self.db.drop_table('idb', confirm=False)
        return True

    def update(self, workers=0.8):
        self.dir.mkdir(parents=True, exist_ok=True)

        print("\n\n\nSTEP 1/3: Checking raw IDB download\n")

        last_download_date = self.status.get('last_download_date')
        if (
            last_download_date is None or 
            last_download_date < self.last_update
        ):
            print(notabs("""
                It looks like your local data is missing or out of date. 
                We will download the latest data from the FJC website.
            """))
            self.download_raw_data()

        print("COMPLETE: Your raw IDB data is up to date.\nFind it here:", self.extracted_data_path)
        
        print("\n\n\nSTEP 2/3: Preprocessing local data\n")

        num_data_rows = None
        num_raw_rows = sum(len(x) for x in self.load_raw_data(usecols=[0], chunksize=100000))
        if self.data_path.exists():
            num_data_rows = sum(len(x) for x in pd.read_csv(self.data_path, usecols=[0], chunksize=100000))
            if num_data_rows != num_raw_rows:
                print("There is a mismatch between your raw and processed data. Re-processing.")
                self.data_path.unlink()

        if not self.data_path.exists():
            chunksize = 200000
            futures = []
            num_workers = cpu_workers(workers)
            print(f"Processing data. We will use {workers} of your cpu cores: {num_workers} workers.")
            num_chunks = math.ceil(num_raw_rows / chunksize)
            progress = tqdm(total=num_chunks * 3, desc="Processing IDB Data")
            with ProcessPoolExecutor(num_workers) as executor:
                for i, chunk in enumerate(self.load_raw_data(chunksize=chunksize)):
                    futures.append(executor.submit(process_chunk, self.dir, chunk, i * chunksize))
                    progress.update(1)
                for _ in as_completed(futures):
                    progress.update(1)
                paths = list(self.dir.glob('chunk.*.csv'))
                for path in paths:
                    data = pd.read_csv(path, low_memory=False)
                    pd_save_or_append(data, self.data_path)
                    path.unlink()
                    progress.update(1)

        print("COMPLETE: Your processed IDB data is up to date.\nFind it here:", self.data_path)

        print("\n\n\nSTEP 3/3: Updating database\n")

        if self.db is None:
            print("SKIPPED\nDONE")
            return

        if num_data_rows is None:
            num_data_rows = sum(len(x) for x in pd.read_csv(self.data_path, usecols=[0], chunksize=100000))
        dtype_map = self.infer_dtypes()

        num_db_rows = 0
        if 'idb' in self.db.t:
            num_db_rows = self.db.t.idb.count()
        
        if num_db_rows != num_data_rows or self.status.get('db_needs_reset'):
            print("There is a mismatch between your database and local data. Rebuilding.")
            if 'idb' in self.db.t:
                self.db.drop_table('idb', confirm=False)
            self.db.create_table('idb')
            self.db.t.idb.add_column('idb_row', 'CharField', unique=True)
            for col, dtype in tqdm(dtype_map.items(), desc="Building Schema"):
                self.db.t.idb.add_column(col, dtype)

            chunksize = 200000
            num_chunks = math.ceil(num_data_rows / chunksize)
            table = self.db.t.idb
            for chunk in tqdm(
                pd.read_csv(self.data_path, chunksize=chunksize, low_memory=False), 
                total=num_chunks, desc="Pushing Data"
            ):
                for col, dtype in dtype_map.items():
                    if dtype == 'DateField':
                        chunk[col] = pd.to_datetime(chunk[col], errors='coerce').dt.date
                chunk = chunk.where(pd.notnull(chunk), None)
                table.add_data(chunk, copy=True)
            self.save_status('db_needs_reset', False)
        print("COMPLETE: Your IDB database is up to date.\nDONE")
        



        



