import distutils.command.build
from importlib.metadata import version as get_package_version
import os
from setuptools import setup, find_packages


PACKAGE_DIR = os.path.dirname(os.path.realpath(__file__))


def get_requirements(filename):
    requirements_path = os.path.join(PACKAGE_DIR, filename)

    with open(requirements_path, 'r') as f:
        lines = f.read().splitlines()
    return [line for line in lines if line and not line.startswith('#')]


def get_version():
    version_path = os.path.join(PACKAGE_DIR, 'docketanalyzer', '_version.py')
    with open(version_path, 'r') as f:
        version = f.read().split('=')[1].strip().strip('"')
        return version


class BuildCommand(distutils.command.build.build):
    def initialize_options(self):
        distutils.command.build.build.initialize_options(self)
        build_dir = os.path.join(PACKAGE_DIR, 'build')
        self.build_base = build_dir


extensions = ['chat', 'core', 'ocr', 'pipelines']

extras_require = {'all': []}
for extension in extensions:
    package_name = f"docketanalyzer_{extension}"
    package_version = get_package_version(package_name)
    requirement = f"docketanalyzer-{extension}>={package_version}"
    extras_require[extension] = [requirement]
    extras_require['all'].append(requirement)


setup(
    name='docketanalyzer',
    version=get_version(),
    description='',
    url='https://github.com/docketanalyzer/docketanalyzer',
    author='Nathan Dahlberg',
    packages=find_packages(PACKAGE_DIR),
    package_data={"docketanalyzer": ["data/*"]},
    include_package_data=True,
    install_requires=get_requirements('requirements.txt'),
    extras_require=extras_require,
    entry_points={
        'console_scripts': [
            'da = docketanalyzer:cli',
        ],
    },
    cmdclass={"build": BuildCommand},
)
