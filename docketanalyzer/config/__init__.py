from .package_config import PackageConfig, ConfigKey
from .config import config


import os
for key in config.keys:
    key.create(globals())
    os.environ[key.name] = str(config[key.name])
