from collections.abc import Generator
from pathlib import Path

import pandas as pd
from tqdm import tqdm

from docketanalyzer import env, load_clients

from .choices import choices
from .docket_batch import DocketBatch
from .docket_manager import DocketManager


class DocketIndex:
    """Index for managing docket data."""

    def __init__(self, data_dir: str | Path | None = None):
        """Initialize DocketIndex."""
        self.data_dir = Path(data_dir or env.DATA_DIR)
        self.dir = self.data_dir / "data" / "dockets"
        self.choices = choices.dict()
        self.values = {
            name: {v: k for k, v in choice.items()}
            for name, choice in self.choices.items()
        }
        self._table = None
        self._pacer = None
        self._recap = None

    # Postgres
    @property
    def db(self):
        """Get the database connection."""
        return load_clients("db")

    @property
    def table(self):
        """Main table for organizing index data."""
        raise NotImplementedError("Fix this")
        if not self._table:
            try:
                table = self.db.t[self.table_name]
            except KeyError:
                self.db.create_table(self.table_name)
                table = self.db.t[self.table_name]
                table.add_column(
                    self.id_col,
                    "CharField",
                    unique=True,
                )
            self._table = table
        return self._table

    # Pacer
    @property
    def pacer(self):
        """Get the Pacer connection."""
        from docketanalyzer.pacer import Pacer

        if not self._pacer:
            self._pacer = Pacer()
        return self._pacer

    # Recap
    @property
    def recap(self):
        """Get the Recap connection."""
        from docketanalyzer.pacer import RecapAPI

        if not self._recap:
            self._recap = RecapAPI(sleep=0.2)
        return self._recap

    # S3
    @property
    def s3(self):
        """Get the S3 connection."""
        s3 = load_clients("s3")
        s3.data_dir = self.data_dir
        return s3

    def push(self, path: str | Path = "", confirm: bool = False, **args):
        """Push the local data to S3."""
        self.s3.push(path=path, confirm=confirm, **args)

    def pull(self, path: str | Path = "", confirm: bool = False, **args):
        """Pull the data from S3 to local."""
        self.s3.pull(path=path, confirm=confirm, **args)

    # Cached IDs
    @property
    def cached_ids_path(self) -> Path:
        """Path to the cached IDs file."""
        return self.dir / "ids.csv"

    def load_cached_ids(self, shuffle: bool = False) -> list[str]:
        """Load cached IDs from the file."""
        raise NotImplementedError("Fix this")
        if not self.cached_ids_path.exists():
            obj_ids = self.table.pandas("docket_id")
            obj_ids.to_csv(self.cached_ids_path, index=False)
        obj_ids = pd.read_csv(self.cached_ids_path)["docket_id"]
        if shuffle:
            obj_ids = obj_ids.sample(frac=1)
        return obj_ids.tolist()

    def reset_cached_ids(self):
        """Reset the cached IDs by deleting the file."""
        if self.cached_ids_path.exists():
            self.cached_ids_path.unlink()

    @property
    def cached_ids(self) -> list[str]:
        """Get the cached IDs."""
        return self.load_cached_ids()

    # Additional utilities
    def add_local_docket_ids(self):
        """Add local directory docket IDs to the index."""
        self.dir.mkdir(parents=True, exist_ok=True)
        docket_ids = pd.DataFrame(
            {
                "docket_id": [
                    x.name
                    for x in self.dir.iterdir()
                    if x.is_dir() and not x.name.startswith(".")
                ]
            }
        )

        self.reset_cached_ids()
        existing_docket_ids = self.cached_ids
        docket_ids = docket_ids[~docket_ids["docket_id"].isin(existing_docket_ids)]

        if len(docket_ids):
            batch_size = 100000
            for i in tqdm(range(0, len(docket_ids), batch_size)):
                batch = docket_ids.iloc[i : i + batch_size]
                self.table.add_data(batch, copy=True)
        self.reset_cached_ids()

    def make_batch(self, docket_ids: list[str]) -> DocketBatch:
        """Create a batch of dockets."""
        return DocketBatch(docket_ids, self)

    def __getitem__(self, docket_id: str) -> DocketManager:
        """Get a DocketManager by ID."""
        return DocketManager(docket_id, index=self)

    def __iter__(self) -> Generator[DocketManager, None, None]:
        """Iterate over all DocketManagers."""
        for docket_id in tqdm(self.load_cached_ids()):
            yield self[docket_id]


def load_docket_index(data_dir: str | Path | None = None) -> DocketIndex:
    """Load the DocketIndex."""
    return DocketIndex(data_dir)
