import distutils.command.build
import os
from setuptools import setup, find_packages


VERSION = os.environ.get('VERSION')
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


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


def get_package_files(packages, exclude=['/docketanalyzer/dev/', '/__pycache__/', '/.']):
    paths = []
    for package in packages:
        package_dir = os.path.join(BASE_DIR, package)
        for (path, directories, filenames) in os.walk(package_dir):
            for filename in filenames:
                path = os.path.join('..', path, filename)
                if not any([e in path for e in exclude]):
                    paths.append(path)
    return list(set(paths))


packages = find_packages(BASE_DIR, exclude=['docketanalyzer.dev*'])
package_files = get_package_files(packages)
for path in package_files:
    print(path)
print('------')
print(packages)

if 0:
    setup(
        name='docketanalyzer',
        version=VERSION,
        description='',
        url='https://github.com/docketanalyzer/docketanalyzer',
        author='Nathan Dahlberg',
        package_dir={'': BASE_DIR},
        packages=packages,
        package_data={'': package_files},
        install_requires=get_requirements('requirements.txt'),
        entry_points={
            'console_scripts': [
                'da = docketanalyzer:cli',
            ],
        },
        cmdclass={"build": BuildCommand},
    )


# python setup.py bdist_wheel
# twine upload dist/*
