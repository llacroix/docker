#!/usr/bin/env python
import argparse
import time
import os
import shlex
import subprocess
import sys
import glob
import pip
import re
from os import path
from os.path import expanduser

try:
    quote = shlex.quote
except Exception as exc:
    def quote(s):
        """Return a shell-escaped version of the string *s*."""
        _find_unsafe = re.compile(r'[^\w@%+=:,./-]').search
        if not s:
            return "''"
        if _find_unsafe(s) is None:
            return s

        # use single quotes, and put single quotes into double quotes
        # the string $'b is then quoted as '$'"'"'b'
        return "'" + s.replace("'", "'\"'\"'") + "'"


def pipe(args):
    """
    Call the process with std(in,out,err)
    """
    process = subprocess.Popen(
        args,
        stdin=sys.stdin,
        stdout=sys.stdout,
        stderr=sys.stderr,
    )

    process.wait()

    return process.returncode


def start():
    """
    Main process running odoo
    """
    #quoted_args = [
    #    quote(arg)
    #    for arg in sys.argv[1:]
    #] or ["true"]
    #username = "odoo"

    # Run the command as odoo while everything is quoted
    #return pipe(["su", username, "-c", " ".join(quoted_args)])
    # TODO parse sys.argv to append addons path if command is odoo
    # we can introspect /addons/* and env ODOO_BASE_PATH to compute
    # the right addons path to pass to the process
    print("Starting odoo", sys.argv)

    return pipe(sys.argv[1:])


def call_sudo_entrypoint():
    ret = pipe(["sudo", "-H", "/sudo-entrypoint.py"])


def install_python_dependencies():
    """
    Install all the requirements.txt file found
    """
    # TODO
    # https://pypi.org/project/requirements-parser/
    # to parse all the requirements file to parse all the possible specs
    # then append the specs to the loaded requirements and dump the requirements.txt
    # file in /var/lib/odoo/requirements.txt and then install this only file
    # instead of calling multiple time pip
    for requirements in glob.glob("/addons/**/requirements.txt"):
        print("Installing python packages from %s" % requirements)
        pip.main(['install', '-r', requirements])


def main():
    # Install apt package first then python packages
    ret = call_sudo_entrypoint()
    print("Return from sudo", ret)
    if ret not in [0, None]:
        sys.exit(ret)

    # Install python packages with pip in user home
    install_python_dependencies()

    return start()

try:
    code = main()
    sys.exit(code)
except Exception as exc:
    print(exc.message)
    sys.exit(1)
except KeyboardInterrupt as exc:
    print(exc.message)
    sys.exit(1)
