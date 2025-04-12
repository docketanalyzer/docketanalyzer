from pathlib import Path

from nates import Config

from .utils import BASE_DIR

env = Config(
    path=Path.home() / ".cache" / "docketanalyzer" / "config.json",
    keys=[
        dict(
            name="DATA_DIR",
            key_type="str",
            description="\nConfigure data\n",
            default=str((BASE_DIR.parent / "data").resolve()),
            group="data",
        ),
    ],
)
