#!/usr/bin/env python
import argparse
import time
import shlex
import subprocess
import sys
import glob
import pip
import re
import string
import random

import os
from os import path
from os.path import expanduser
import configparser

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


def randomString(stringLength=10):
    """Generate a random string of fixed length """
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(stringLength))

def install_master_password(config_path):
    # Secure an odoo instance with a default master password
    # if required we can update the master password but at least
    # odoo doesn't get exposed by default without master passwords
    from passlib.context import CryptContext

    config = configparser.ConfigParser()
    config.read(config_path)
    pgpass_secret = path.join(path.expanduser('~'), ".pgpass")

    master_password_secret = "/run/secrets/master_password"
    if path.exists(pgpass_secret):
        with open(master_password_secret, "r") as mp:
            master_password = mp.read().strip()
    elif os.environ.get('MASTER_PASSWORD'):
        master_password = os.environ.get('MASTER_PASSWORD')
    else:
        ctx = CryptContext(['pbkdf2_sha512'])
        master_password = ctx.encrypt(randomString(16))

    config.set('options', 'admin_passwd', master_password)

    with open(config_path, 'w') as out:
        config.write(out)

def setup_environ(config_path):
    config = configparser.ConfigParser()
    config.read(config_path)

    def check_config(config_name, config_small):
        """
        Check if config is in odoo_rc or command line
        """
        value = None

        if config['options'].get(config_name):
            value = config['options'].get(config_name)

        if not value and '--%s' % config_name in sys.argv:
            idx = sys.argv.index('--%s' % config_name)
            value = sys.argv[idx+1] if idx < len(sys.argv) else None

        if not value and config_small and '-%s' % config_small in sys.argv:
            idx = sys.argv.index('-%s' % config_small)
            value = sys.argv[idx+1] if idx < len(sys.argv) else None

        return value

    variables = [
        ('PGUSER', 'db_user', 'r'),
        ('PGHOST', 'db_host', None),
        ('PGPORT', 'db_port', None),
        ('PGDATABASE', 'database', 'd')
    ]

    # Setup basic PG env variables to simplify managements
    # combined with secret pg pass we can use psql directly
    for pg_val, odoo_val, small_arg in variables:
        value = check_config(odoo_val, small_arg)
        if value:
            os.environ[pg_val] = value

def main():
    # Install apt package first then python packages
    ret = call_sudo_entrypoint()
    print("Return from sudo", ret)
    if ret not in [0, None]:
        sys.exit(ret)

    # Install python packages with pip in user home
    install_python_dependencies()
    install_master_password(os.environ['ODOO_RC'])
    setup_environ(os.environ['ODOO_RC'])

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
