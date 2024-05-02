import re
import os
from setuptools import setup, find_packages
import toml
def sync_version(directory,version):
    furl = os.path.join(directory,'pyproject.toml')
    with open(furl, 'r') as file:
        data = toml.load(file)
    data['project']['version'] = version

    with open(furl, 'w') as file:
        toml.dump(data, file)


def get_version():
    """
    Reads the version string from the package __init__.py file.
    """
    directory = os.path.abspath(os.path.dirname(__file__))
    init_path = os.path.join(directory,'src','specs', '__init__.py')
    with open(init_path, 'r') as file:
        version_file_contents = file.read()
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]", version_file_contents, re.M)
    if version_match:
        sync_version(directory,version_match.group(1))
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")

setup(
    name='specs',
    version=get_version(),
    package_dir={'': 'src'},
    packages=find_packages(where='src'),
)
