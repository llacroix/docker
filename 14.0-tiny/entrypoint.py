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
import signal
from passlib.context import CryptContext

try:
    from pip._internal.network.session import PipSession
    from pip._internal.req.req_file import parse_requirements
except Exception:
    from pip.download import PipSession
    from pip.req.req_file import parse_requirements
from collections import defaultdict

try:
    # python3
    SIGSEGV = signal.SIGSEGV.value
except AttributeError:
    SIGSEGV = signal.SIGSEGV


try:
    # python3
    from configparser import ConfigParser, NoOptionError
except Exception:
    from ConfigParser import ConfigParser, NoOptionError


try:
    # python3
    quote = shlex.quote
except Exception:
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


class Requirement(object):
    def __init__(self):
        self.extras = set()
        self.specifiers = set()


def merge_requirements(files):
    requirements = defaultdict(lambda: Requirement())
    links = set()

    for filename in files:
        for requirement in parse_requirements(filename, session=PipSession()):
            if not hasattr(requirement.req, 'name'):
                links.add(requirement.link.url)
                break
            name = requirement.req.name
            specifiers = requirement.req.specifier
            extras = requirement.req.extras
            requirements[name].extras |= set(extras)
            requirements[name].specifiers |= set(specifiers)

    result = []
    for key, value in requirements.items():
        if not value.extras:

            result.append("%s %s" % (key, ",".join(map(str, value.specifiers))))
        else:
            result.append("%s [%s] %s" % (
                key,
                ",".join(map(str, value.extras)),
                ",".join(map(str, value.specifiers))
            ))

    for link in links:
        result.append(link)

    return "\n".join(result)

def pipe(args):
    """
    Call the process with std(in,out,err)
    """
    print("Executing external command %s" % " ".join(args))
    flush_streams()

    env = os.environ.copy()

    process = subprocess.Popen(
        args,
        stdin=sys.stdin,
        stdout=sys.stdout,
        stderr=sys.stderr,
        env=env
    )

    process.wait()

    print(
        (
            "External command execution completed with returncode(%s)"
        ) % process.returncode
    )

    if process.returncode == -SIGSEGV:
        print("PIPE call segfaulted")
        print("Failed to execute %s" % args)

    # Force a flush of buffer
    flush_streams()

    return process.returncode


def start():
    """
    Main process running odoo
    """
    print("Starting main command", sys.argv)

    return pipe(sys.argv[1:])


def call_sudo_entrypoint():
    command = ["sudo", "-H", "-E"]
    args = ["/sudo-entrypoint.py"]

    #env_args = [
    #    "%s=%s" % (key, value)
    #    for key, value in os.environ.items()
    #]

    ret = pipe(
        command +
        #env_args +
        args
    )

    #ret = pipe(["sudo", "-E", "-H", "/sudo-entrypoint.py"])
    return ret


def install_python_dependencies():
    """
    Install all the requirements.txt file found
    """
    # TODO
    # https://pypi.org/project/requirements-parser/
    # to parse all the requirements file to parse all the possible specs
    # then append the specs to the loaded requirements and dump
    # the requirements.txt file in /var/lib/odoo/requirements.txt and
    # then install this only file instead of calling multiple time pip
    requirement_files = glob.glob("/addons/**/requirements.txt")
    requirement_files.sort()

    print("Installing python requirements found in:")
    print("    \n".join(requirement_files))

    req_file = '/var/lib/odoo/requirements.txt'
    with open(req_file, 'w') as fout:
        data = merge_requirements(requirement_files)
        fout.write(data)

    for requirements in requirement_files:
        print("Installing python packages from %s" % requirements)
        flush_streams()
        # pip.main(['install', '-r', requirements])
        #pipe(["pip", "install", "-r", requirements])
        #print("Done")
        #flush_streams()

    print(data)
    flush_streams()

    os.environ['PATH'] = "/var/lib/odoo/.local/bin:%s" % (os.environ['PATH'],)
    pipe(["pip", "install", "--user", "-r", req_file])
    flush_streams()

    print("Installing python requirements complete\n")
    flush_streams()


def randomString(stringLength=10):
    """Generate a random string of fixed length """
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(stringLength))


def install_master_password(config_path):
    # Secure an odoo instance with a default master password
    # if required we can update the master password but at least
    # odoo doesn't get exposed by default without master passwords
    print("Installing master password in ODOORC")

    ctx = CryptContext(
        ['pbkdf2_sha512', 'plaintext'],
        deprecated=['plaintext']
    )
    config = ConfigParser()
    config.read(config_path)

    master_password_secret = "/run/secrets/master_password"
    if path.exists(master_password_secret):
        with open(master_password_secret, "r") as mp:
            master_password = mp.read().strip()
    elif os.environ.get('MASTER_PASSWORD'):
        master_password = os.environ.get('MASTER_PASSWORD')
    else:
        master_password = randomString(64)

        if os.environ.get('DEPLOYMENT_AREA') == 'undefined':
            print(
                "Use this randomly generated master password"
                " to manage the database"
            )
            print("    %s" % master_password)

    # Check that we don't have plaintext and encrypt it
    # This allow us to quickly setup servers without having to hash
    # ourselves first for security reason, you should always hash
    # the password first and not expect the image to do it correctly
    # but older version of odoo do not support encryption so only encrypt
    # older version of odoo...
    if (
        float(os.environ.get('ODOO_VERSION')) > 10 and
        ctx.identify(master_password) == 'plaintext'
    ):
        master_password = ctx.encrypt(master_password)

    config.set('options', 'admin_passwd', master_password)

    with open(config_path, 'w') as out:
        config.write(out)

    print("Installing master password completed")

    flush_streams()


def get_dirs(cur_path):
    return [
        path.join(cur_path, npath)
        for npath in os.listdir(cur_path)
        if path.isdir(path.join(cur_path, npath))
    ]


def setup_addons_paths(config_path):
    base_addons = os.environ.get('ODOO_BASE_PATH')

    addons = os.listdir('/addons')

    valid_paths = [base_addons]

    addons_paths = get_dirs('/addons')
    for addons_path in addons_paths:
        print("Lookup addons in %s" % addons_path)
        flush_streams()
        addons = get_dirs(addons_path)
        for addon in addons:
            files = os.listdir(addon)
            if (
                '__init__.py' in files and
                '__manifest__.py' in files or
                '__openerp__.py' in files
            ):
                valid_paths.append(addons_path)
                print("Addons found !")
                flush_streams()
                break
        if addons_path in valid_paths:
            continue
        else:
            print("No addons found in path. Skipping...")
            flush_streams()

    config = ConfigParser()
    config.read(config_path)
    config.set('options', 'addons_path', ",".join(valid_paths))
    with open(config_path, 'w') as out:
        config.write(out)

    flush_streams()


def setup_environ(config_path):
    print("Configuring environment variables for postgresql")
    config = ConfigParser()
    config.read(config_path)

    def get_option(config, section, name):
        try:
            return config.get(section, name)
        except NoOptionError:
            return None

    def check_config(config_name, config_small):
        """
        Check if config is in odoo_rc or command line
        """
        value = None

        if get_option(config, 'options', config_name):
            value = get_option(config, 'options', config_name)

        if not value and '--%s' % config_name in sys.argv:
            idx = sys.argv.index('--%s' % config_name)
            value = sys.argv[idx + 1] if idx < len(sys.argv) else None

        if not value and config_small and '-%s' % config_small in sys.argv:
            idx = sys.argv.index('-%s' % config_small)
            value = sys.argv[idx + 1] if idx < len(sys.argv) else None

        return value

    variables = [
        ('PGUSER', 'db_user', 'r'),
        ('PGHOST', 'db_host', None),
        ('PGPORT', 'db_port', None),
        ('PGDATABASE', 'database', 'd')
    ]

    # Accpet db_password only with this if some infra cannot be setup otherwise...
    # It's a bad idea to pass password in cleartext in command line or
    # environment variables so please use .pgpass instead...
    if os.environ.get('I_KNOW_WHAT_IM_DOING') == 'TRUE':
        variables.append(
            ('PGPASSWORD', 'db_password', 'w')
        )

    # Setup basic PG env variables to simplify managements
    # combined with secret pg pass we can use psql directly
    for pg_val, odoo_val, small_arg in variables:
        value = check_config(odoo_val, small_arg)
        if value:
            os.environ[pg_val] = value

    print("Configuring environment variables done")
    flush_streams()


def wait_postgresql():
    import psycopg2

    retries = int(os.environ.get('PGRETRY', 5))
    retries_wait = int(os.environ.get('PGRETRYTIME', 1))
    error = None

    # Default database set to postgres
    if not os.environ.get('PGDATABASE'):
        os.environ['PGDATABASE'] = 'postgres'

    for retry in range(retries):
        try:
            print("Trying to connect to postgresql")
            # connect using defined env variables and pgpass files
            flush_streams()
            conn = psycopg2.connect("")
            message = "  Connected to %(user)s@%(host)s:%(port)s"
            print(message % conn.get_dsn_parameters())
            flush_streams()
            break
        except psycopg2.OperationalError as exc:
            error = exc
            time.sleep(retries_wait)
    else:
        # we reached the maximum retries so we trigger failure mode
        if error:
            print("Database connection failure %s" % error)
            flush_streams()

        sys.exit(1)


def main():
    # Install apt package first then python packages
    ret = call_sudo_entrypoint()

    if ret not in [0, None]:
        sys.exit(ret)

    # Install python packages with pip in user home
    install_python_dependencies()
    install_master_password(os.environ.get('ODOO_RC'))
    setup_environ(os.environ.get('ODOO_RC'))
    setup_addons_paths(os.environ.get('ODOO_RC'))

    if not os.environ.get('ODOO_SKIP_POSTGRES_WAIT'):
        wait_postgresql()

    return start()


def flush_streams():
    sys.stdout.flush()
    sys.stderr.flush()


try:
    code = main()
    flush_streams()
    sys.exit(code)
except Exception as exc:
    print(exc)
    import traceback
    traceback.print_exc()
    flush_streams()
    sys.exit(1)
except KeyboardInterrupt as exc:
    print(exc)
    import traceback
    traceback.print_exc()
    flush_streams()
    sys.exit(1)
