import os
import shutil
import click
from pathlib import Path
import docketanalyzer
from docketanalyzer import PYPI_TOKEN, package_data


def parse_version(version_str):
    return tuple(map(int, version_str.split('.')))


def is_valid_increment(v1, v2):
    if v1 == v2:
        return True, "Versions are identical"
    
    for i in range(3):
        if v2[i] > v1[i]:
            if v2[i] == v1[i] + 1 and v2[i+1:] == (0,) * (2-i):
                return True, f"Valid increment at {'major' if i == 0 else 'minor' if i == 1 else 'patch'} level"
            else:
                return False, "Invalid increment"
        elif v2[i] < v1[i]:
            return False, "Second version is lower"
    
    return False, "Other issue"


def compare_versions(version1, version2):
    v1 = parse_version(version1)
    v2 = parse_version(version2)
    
    result, message = is_valid_increment(v1, v2)
    return result, message


def update_version(version):
    while 1:
        new_version = input(f"Current version is {version}. Enter new version or leave blank to keep: ")
        if not new_version:
            new_version = version
        result, message = compare_versions(version, new_version)
        if result:
            break
        print('Invalid version change:', message)
    return new_version


@click.command()
@click.option('--push', is_flag=True, help="Push to PyPI after building")
def build(push):
    """
    Build and / or push docketanalyzer.
    """
    package_dir = Path(__file__).parents[2]
    build_dir = package_dir / 'build'
    dist_dir = package_dir / 'dist'
    if build_dir.exists():
        shutil.rmtree(build_dir)
    if dist_dir.exists():
        shutil.rmtree(dist_dir)

    setup_path = package_dir / 'setup.py'
    version = update_version(docketanalyzer.__version__)
    version_path = package_dir / 'docketanalyzer' / '_version.py'
    version_path.write_text(f'__version__ = "{version}"\n')

    cmd = f"cd {package_dir} && python {setup_path} bdist_wheel --dist-dir={dist_dir}"
    os.system(cmd)
    
    if push:
        cmd = f"pip install -e {package_dir}"
        os.system(cmd)

        cmd = f"twine upload {dist_dir}/*"
        if PYPI_TOKEN is not None:
            cmd += f" -u __token__ -p {PYPI_TOKEN}"
        os.system(cmd)
    
        shutil.rmtree(build_dir)
        shutil.rmtree(dist_dir)
