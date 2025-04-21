from collections.abc import Generator
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .docket_index import DocketIndex
    from .docket_manager import DocketManager


class DocketBatch:
    """Batch manager for a collection of dockets.

    Used for operations that are more efficient in bulk.
    """

    def __init__(self, docket_ids: list[str], index: "DocketIndex"):
        """Initialize DocketBatch."""
        self.docket_ids = docket_ids
        self.index = index

    def __iter__(self) -> Generator["DocketManager", None, None]:
        """Iterate over the DocketManagers in the batch."""
        for docket_id in self.docket_ids:
            yield self.index[docket_id]

    def __getattribute__(self, name: str):
        """Passthrough attributes from the index."""
        index_attributes = ["db", "table", "s3"]
        if name in index_attributes:
            return getattr(object.__getattribute__(self, "index"), name)

        return object.__getattribute__(self, name)
