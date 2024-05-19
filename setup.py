import os
from setuptools import setup, find_packages


def get_requirements(filename):
    dir_path = os.path.dirname(os.path.realpath(__file__))
    requirements_path = os.path.join(dir_path, filename)

    with open(requirements_path, 'r') as f:
        lines = f.read().splitlines()
    return [line for line in lines if line and not line.startswith('#')]


setup(
    name='docketanalyzer',
    version='0.1.1',
    description='',
    url='https://github.com/docketanalyzer/docketanalyzer',
    author='Nathan Dahlberg',
    package_dir={'': '.'},
    packages=find_packages('.'),
    install_requires=get_requirements('requirements.txt'),
    entry_points={
        'console_scripts': [
            'da = docketanalyzer:cli',
        ],
    },
)


# python setup.py bdist_wheel
# twine upload dist/*
