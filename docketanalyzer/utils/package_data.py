import pandas as pd
from pathlib import Path
from .registry import Registry


PACKAGE_DATA_DIR = Path(__file__).parents[1] / 'package_data'


class PackageData:
    name = None
    data_path = '.'

    @property
    def path(self):
        return PACKAGE_DATA_DIR / self.data_path
    
    def load(self):
        raise NotImplementedError


class PackageDataRegistry(Registry):
    def find_filter(self, obj):
        return (
            isinstance(obj, type) and
            issubclass(obj, PackageData) and
            obj is not PackageData and
            obj.name is not None
        )


package_data_registry = PackageDataRegistry()


def package_data(name=None):
    for package_data in package_data_registry.all():
        if package_data.name == name:
            return package_data()
    if name is not None:
        print(f"Could not find package data with name '{name}'")
    print("Available package data:")
    for package_data in package_data_registry.all():
        print(f"  {package_data.name}")


class SALIData(PackageData):
    name = 'sali'
    data_path = 'sali.csv'

    def load(self):
        if self.path.exists():
            return pd.read_csv(self.path)


class ExampleComplaint(PackageData):
    name = 'example-complaint'
    data_path = 'example-complaint.pdf'

    def load(self):
        if self.path.exists():
            return self.path.read_bytes()
