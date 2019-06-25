#!/usr/bin/env python3

import configparser
from pathlib import Path
import shutil
import sys
import zipapp

import pep517.build
import twine

# The "proper" way to handle the default would be to check python_requires
# in setup.cfg. But, since Bork needs Python 3, there's no point.
DEFAULT_PYTHON_INTERPRETER = "/usr/bin/env python3"

def print_help():
    print("Usage: bork build")
    print("       bork clean")
    print("       bork release [pypi] [github]")

def load_setup_cfg():
    setup_cfg = configparser.ConfigParser()
    setup_cfg.read('setup.cfg')
    return setup_cfg

def build_pep517(args):
    pep517.build.main(pep517.build.parser.parse_args('.', *args))

def build_zipapp(args):
    config = load_setup_cfg()
    name = config['metadata']['name']

    # The code is assumed to be in ./<name>
    source = str(Path(name))

    # TODO: Get version info -- this is more complex, since it can be in many places.
    #target = "dist/{}-{}.pyz".format(name, version)
    target = "dist/{}.pyz".format(name)

    # To override the default interpreter, add this to your project's setup.cfg:
    #
    # [bork]
    # python_interpreter = /path/to/python
    if 'bork' in config and 'python_interpreter' in config['bork']:
        interpreter = config['bork']['python_interpreter']
    else:
        interpreter = DEFAULT_PYTHON_INTERPRETER

    # TODO: Allow the ability to specify which console_script entrypoint to
    #       use, instead of duplicating it.
    main = config['bork']['zipapp_entrypoint']

    zipapp.create_archive(source, target, interpreter, main)
    if not Path(target).exists():
        raise Exception("Failed to build zipapp: {}".format(target))

def build(args):
    build_pep517(args)
    build_zipapp(args)

def _try_delete(path):
    if Path(path).is_dir():
        shutil.rmtree(path)
    elif Path(path).exists():
        raise Exception("{} is not a directory".format(path))

def clean(args):
    config = load_setup_cfg()
    name = config['metadata']['name']

    # TODO: Delete ./build ./dist ./<name>.egg-info
    _try_delete("./build")
    _try_delete("./dist")
    _try_delete("./{}.egg-info".format(name))

def release(args):
    print("Would release to: {}".format(str(args)))
    raise NotImplementedError("bork release")

def main(argv=None):
    if argv is None:
        argv = sys.argv

    if len(argv) < 1 or "-h" in argv or "--help" in argv:
        print_help()
        exit(1)

    command = argv[1]
    args = argv[2:]

    if command == "build":
        build(args)
    elif command == "build-pep517":
        build_pep517(args)
    elif command == "build-zipapp":
        build_zipapp(args)
    elif command == "clean":
        clean(args)
    elif command == "release":
        release(args)
    else:
        print_help()

if __name__ == "__main__":
    main()
