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


def install_apt_packages():
    """
    Install debian dependencies.
    """
    package_list = set()

    for packages in glob.glob("/addons/**/apt-packages.txt"):
        print("Installing packages from %s" % packages)
        with open(packages, 'r') as pack_file:
            lines = [line.strip() for line in pack_file]         
            package_list.update(set(lines))
        
    if len(package_list) > 0:
        ret = pipe(['apt-get', 'update'])

        # Something went wrong, stop the service as it's failing
        if ret != 0:
            sys.exit(ret)

        ret = pipe(['apt-get', 'install', '-y'] + list(package_list))

        # Something went wrong, stop the service as it's failing
        if ret != 0:
            sys.exit(ret)


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


def load_secrets():
    # TODO add a way to load some secrets so odoo process can
    # use secrets as a way to load passwords/user for postgresql
    # credentials could also be stored in the HOME of the odoo user
    # except we cannot rely on secrets 100% because it only works in
    # swarm mode
    pass


def start():
    """
    Main process running odoo
    """
    quoted_args = [
        quote(arg)
        for arg in sys.argv[1:]
    ] or ["true"]
    username = "odoo"

    # Run the command as odoo while everything is quoted
    return pipe(["su", username, "-c", " ".join(quoted_args)])

def fix_access_rights():
    pipe(["chown", "-R", "odoo:odoo", "/var/lib/odoo"])
    pipe(["chown", "-R", "odoo:odoo", "/etc/odoo"])


def main():
    install_apt_packages()
    install_python_dependencies()
    load_secrets()
    fix_access_rights()
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
