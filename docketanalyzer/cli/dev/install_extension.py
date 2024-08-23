import os
import site
import sys
import click
from pathlib import Path
import simplejson as json


def create_egg_link(package_name, package_path):
    site_packages = site.getsitepackages()[0]
    egg_link_path = os.path.join(site_packages, f"{package_name}.egg-link")
    with open(egg_link_path, "w") as f:
        f.write(str(package_path))
        f.write("\n.")


def update_easy_install_pth(package_path):
    site_packages = site.getsitepackages()[0]
    easy_install_path = os.path.join(site_packages, "easy-install.pth")
    with open(easy_install_path, "a+") as f:
        f.seek(0)
        content = f.read()
        if str(package_path) not in content:
            f.write(f"\n{package_path}\n")


@click.command()
@click.argument('extension_name')
def install_extension(extension_name):
    """
    Install extension in editable mode for development.
    """
    package_name = 'docketanalyzer_' + extension_name
    extensions_dir = Path(__file__).parents[3] / 'extensions'
    package_dir = extensions_dir / package_name
    config_path = package_dir / 'build_config.json'
    build_config = json.loads(config_path.read_text())

    create_egg_link(package_name, extensions_dir)
    update_easy_install_pth(extensions_dir)

    sys.path.insert(0, str(extensions_dir))

    requirements = ' '.join(build_config['install_requires'])
    os.system(f"pip install {requirements}")

    click.echo(f"{extension_name} extension installed.")
