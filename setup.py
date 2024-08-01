import distutils.command.build
import os
from setuptools import setup, find_packages


VERSION = os.environ.get('VERSION')
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE_DIR)


class BuildCommand(distutils.command.build.build):
    def initialize_options(self):
        distutils.command.build.build.initialize_options(self)
        self.build_base = os.path.join(BASE_DIR, 'build', 'build')


def get_requirements(filename):
    dir_path = os.path.dirname(os.path.realpath(__file__))
    requirements_path = os.path.join(dir_path, filename)

    with open(requirements_path, 'r') as f:
        lines = f.read().splitlines()
    return [line for line in lines if line and not line.startswith('#')]


setup(
    name='docketanalyzer',
    version=VERSION,
    description='',
    url='https://github.com/docketanalyzer/docketanalyzer',
    author='Nathan Dahlberg',
    packages=['docketanalyzer'],
    include_package_data=True,
    install_requires=get_requirements('requirements.txt'),
    entry_points={
        'console_scripts': [
            'da = docketanalyzer:cli',
        ],
    },
    cmdclass={"build": BuildCommand},
    manifest_dir=BASE_DIR,
)

# python setup.py bdist_wheel
# twine upload dist/*