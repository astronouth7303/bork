from pathlib import Path
from signal import Signals
import subprocess

import toml

from . import builder
from . import github
from . import pypi
from .filesystem import try_delete
from .log import logger


DOWNLOAD_SOURCES = {
    'gh': github,
    'github': github,
    'pypi': pypi.PRODUCTION,
    'pypi-test': pypi.TESTING,
}


def build():
    builder.dist()
    builder.zipapp()


def clean():
    try_delete("./build")
    try_delete("./dist")
    for name in Path.cwd().glob('*.egg-info'):
        if name.is_dir():
            try_delete(name)


def download(package, release_tag, file_pattern, directory):
    if file_pattern is None or len(file_pattern) == 0:
        raise ValueError('file_pattern must be non-empty.')

    if ':' not in package:
        raise ValueError('Invalid package/repository -- no source given.')

    source, package = package.split(':')

    if source not in DOWNLOAD_SOURCES.keys():
        raise ValueError('Invalid package/repository -- unknown source given.')

    source = DOWNLOAD_SOURCES[source]
    source.download(package, release_tag, file_pattern, directory)


def release(test_pypi, dry_run):
    pyproject = toml.load('pyproject.toml')

    try:
        release_dict = pyproject['tool']['bork']['release']
        strip_zipapp_version = release_dict.get('strip_zipapp_version', False)
    except KeyError:
        # Not an error.
        strip_zipapp_version = False

    try:
        release_dict = pyproject['tool']['bork']['release']
        release_to_github = release_dict.get('github', False)
        release_to_pypi = release_dict.get('pypi', True)
    except KeyError:
        release_to_github = False
        release_to_pypi = True

    if not release_to_github and not release_to_pypi:
        print("Configured to release to neither PyPi nor GitHub?")

    if release_to_pypi:
        if test_pypi:
            pypi_instance = pypi.TESTING
        else:
            pypi_instance = pypi.PRODUCTION
        pypi_instance.upload('./dist/*.tar.gz', './dist/*.whl', dry_run=dry_run)

    if release_to_github:
        github.upload('./dist/*.pyz',
                      dry_run=dry_run,
                      strip_zipapp_version=strip_zipapp_version)


def run(alias):
    pyproject = toml.load('pyproject.toml')

    try:
        command = pyproject['tool']['bork']['aliases'][alias]
    except KeyError:
        raise RuntimeError("No such alias: '{}'".format(alias))

    logger().info("Running '%s'", command)

    try:
        subprocess.run(command, check=True, shell=True)

    except subprocess.CalledProcessError as error:
        if error.returncode < 0:
            signal = Signals(- error.returncode)
            msg = "command '{}' exited due to signal {} ({})".format(
                error.cmd, signal.name, signal.value,
            )

        else:
            msg = "bork: command '{}' exited with error code {}".format(
                error.cmd, error.returncode,
            )

        raise RuntimeError(msg) from error
