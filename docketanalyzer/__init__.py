from docketanalyzer.lazy import lazy_load_modules


extensions = ['chat', 'core', 'ocr', 'pipelines']
extension_modules = {}
available_extensions = []
patches = {}
__all__ = []


for extension in extensions:
    extension_module = f'docketanalyzer_{extension}'
    try:
        names = __import__(extension_module).modules
        names = sum(names.values(), [])
        __all__.extend(names)
        extension_modules[extension_module] = names
        available_extensions.append(extension)
        patches[extension] = __import__(extension_module).patch_cli
    except (ModuleNotFoundError, AttributeError):
        pass


lazy_load_modules(extension_modules, globals())


from docketanalyzer._version import __version__
from docketanalyzer.config import PackageConfig, ConfigKey, config
import docketanalyzer.utils as utils
from docketanalyzer.registry import Registry
import docketanalyzer.choices as choices
from docketanalyzer.cli import cli


for patch in patches.values():
    patch(cli)

__all__ += [
    'lazy_load_modules',
    'PackageConfig', 'ConfigKey', 'config',
    'utils', 'Registry', 'choices',
    'cli', 'extensions', 'available_extensions',
]
