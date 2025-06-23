import re
import shutil
import subprocess
from pathlib import Path

import click
import tomli

from docketanalyzer import env


def parse_version(version_str):
    """Parse a version string into a tuple of integers."""
    return tuple(map(int, version_str.split(".")))


def is_valid_increment(v1, v2):
    """Check if the second version is a valid increment of the first version."""
    if v1 == v2:
        return True, "Versions are identical"

    for i in range(3):
        if v2[i] > v1[i]:
            if v2[i] == v1[i] + 1 and v2[i + 1 :] == (0,) * (2 - i):
                return True, "Valid version increment."
            else:
                return False, "Invalid increment"
        elif v2[i] < v1[i]:
            return False, "Second version is lower"

    return False, "Other issue"


def update_version(version, pyproject_path):
    """Update the version in the pyproject.toml file."""
    while 1:
        new_version = input(
            f"Current version is {version}. Enter new version or leave blank to keep: "
        )
        if not new_version:
            new_version = version

        v1 = parse_version(version)
        v2 = parse_version(new_version)
        result, message = is_valid_increment(v1, v2)
        if result:
            break
        print("Invalid version change:", message)

    content = pyproject_path.read_text()
    new_content = re.sub(
        r'version = ".*"', f'version = "{new_version}"', content, count=1
    )
    pyproject_path.write_text(new_content)
    return new_version


@click.command()
@click.option("--push", is_flag=True, help="Push to PyPI after building")
def build(push):
    """Build and / or push docketanalyzer."""
    package_dir = Path(__file__).parents[3]
    dist_dir = package_dir / "dist"
    if dist_dir.exists():
        shutil.rmtree(dist_dir)

    pyproject_path = package_dir / "pyproject.toml"
    pyproject_data = tomli.loads(pyproject_path.read_text(encoding="utf-8"))
    version = pyproject_data["project"]["version"]
    version = update_version(version, pyproject_path)

    subprocess.run(
        ["python", "-m", "build", "--wheel", "--outdir", dist_dir],
        cwd=package_dir,
        check=True,
    )

    if push:
        subprocess.run(["pip", "install", "-e", package_dir], check=True)

        upload_cmd = ["twine", "upload"]
        upload_cmd.extend(str(p) for p in dist_dir.glob("*"))
        if env.PYPI_TOKEN is not None:
            upload_cmd.extend(["-u", "__token__", "-p", env.PYPI_TOKEN])
        subprocess.run(upload_cmd, check=True)
        shutil.rmtree(dist_dir)
