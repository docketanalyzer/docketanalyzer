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
        raise NotImplementedError()


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
    return PackageData()


class Extensions(PackageData):
    name = 'extensions'
    data_path = 'extensions.txt'

    def load(self):
        if self.path.exists():
            return [x.strip() for x in self.path.read_text().split('\n')]
        return []
