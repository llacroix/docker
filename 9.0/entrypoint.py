#!/usr/bin/env python
# import argparse
import time
import shlex
import subprocess
import sys
import glob
# import pip
import re
import string
import random

import os
from os import path
# from os.path import expanduser
import signal
from passlib.context import CryptContext
from contextlib import contextmanager

try:
    from pathlib import Path
except ImportError:
    from pathlib2 import Path

try:
    from pip._internal.network.session import PipSession
    from pip._internal.req.req_file import parse_requirements
    from pip._internal.req.constructors import (
        install_req_from_parsed_requirement
    )
except Exception:
    from pip.download import PipSession
    from pip.req.req_file import parse_requirements

    def install_req_from_parsed_requirement(req):
        return req

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
        self.links = set()
        self.editable = False


def merge_requirements(files):
    requirements = defaultdict(lambda: Requirement())
    links = set()

    for filename in files:
        f_requirements = parse_requirements(
            str(filename), session=PipSession()
        )
        for parsed_requirement in f_requirements:
            requirement = install_req_from_parsed_requirement(
                parsed_requirement
            )

            if requirement.markers and not requirement.markers.evaluate():
                continue

            if not hasattr(requirement.req, 'name'):
                links.add(requirement.link.url)
                break
            name = requirement.req.name
            specifiers = requirement.req.specifier
            extras = requirement.req.extras
            requirements[name].extras |= set(extras)
            requirements[name].specifiers |= set(specifiers)
            if requirement.link:
                requirements[name].links |= {requirement.link.url}
            requirements[name].editable |= requirement.editable

    result = []
    for key, value in requirements.items():
        if value.links:
            result.append("%s" % value.links.pop())
        elif not value.extras:
            result.append(
                "%s %s" % (key, ",".join(map(str, value.specifiers)))
            )
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

    ret = pipe(command + args)

    return ret


def get_all_manifests():
    odoo_manifests = glob.glob('/addons/**/__manifest__.py', recursive=True)
    erp_manifest = glob.glob('/addons/**/__openerp__.py', recursive=True)

    return odoo_manifests + erp_manifest


def module_name(manifest_file):
    return path.basename(path.dirname(manifest_file))


def get_module(manifest_file):
    with open(manifest_file) as manifest_in:
        try:
            code = compile(manifest_in.read(), '__manifest__', 'eval')
            module = eval(code, {}, {})
        except Exception:
            module = {}

    return module


def is_installable(manifest):
    return manifest.get('installable', True)


def is_server_wide(manifest):
    return manifest.get('server_wide', False)


def get_server_wide_modules(manifests):
    base_server_wide_modules = ['base', 'web']
    custom_server_wide_modules = [
        module_name(filename)
        for filename, module in manifests.items()
        if is_server_wide(module)
    ]
    return base_server_wide_modules + custom_server_wide_modules


def install_python_dependencies(valid_paths):
    """
    Install all the requirements.txt file found
    """
    # TODO
    # https://pypi.org/project/requirements-parser/
    # to parse all the requirements file to parse all the possible specs
    # then append the specs to the loaded requirements and dump
    # the requirements.txt file in /var/lib/odoo/requirements.txt and
    # then install this only file instead of calling multiple time pip
    # all_paths = ['/addons'] + get_extra_paths()

    requirement_files = []

    for addons_path in valid_paths:
        cur_path = Path(addons_path)
        requirement_files += cur_path.glob("**/requirements.txt")

    requirement_files = list(set(requirement_files))
    requirement_files.sort()

    print("Installing python requirements found in:")
    for f_path in requirement_files:
        print("    {}".format(str(f_path)))

    req_file = Path('/var/lib/odoo/requirements.txt')
    with req_file.open('w') as fout:
        data = merge_requirements(requirement_files)
        fout.write(data)

    for requirements in requirement_files:
        print("Installing python packages from %s" % requirements)
        flush_streams()

    print(data)
    flush_streams()

    os.environ['PATH'] = "/var/lib/odoo/.local/bin:%s" % (os.environ['PATH'],)
    retcode = pipe(["pip", "install", "--user", "-r", str(req_file)])
    flush_streams()

    if os.environ.get('ODOO_STRICT_MODE') and retcode != 0:
        raise Exception("Failed to install pip dependencies")

    print("Installing python requirements complete\n")
    flush_streams()


def randomString(stringLength=10):
    """Generate a random string of fixed length """
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(stringLength))


def install_master_password(config):
    # Secure an odoo instance with a default master password
    # if required we can update the master password but at least
    # odoo doesn't get exposed by default without master passwords
    print("Installing master password in ODOORC")

    ctx = CryptContext(
        ['pbkdf2_sha512', 'plaintext'],
        deprecated=['plaintext']
    )

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

    print("Installing master password completed")

    flush_streams()


def get_dirs(cur_path):
    return [
        path.join(cur_path, npath)
        for npath in os.listdir(cur_path)
        if path.isdir(path.join(cur_path, npath))
    ]


def get_extra_paths():
    extra_paths = os.environ.get('ODOO_EXTRA_PATHS')

    if not extra_paths:
        return []

    return [
        extra_path.strip()
        for extra_path in extra_paths.split(',')
    ]


def get_valid_paths():
    base_addons = os.environ.get('ODOO_BASE_PATH')

    # addons = os.listdir('/addons')

    valid_paths = [base_addons]

    addons_paths = get_dirs('/addons')
    addons_paths += get_extra_paths()

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

    return valid_paths


def setup_addons_paths(config, valid_paths):
    config.set('options', 'addons_path', ",".join(valid_paths))
    flush_streams()


def setup_server_wide_modules(config):
    print("Searching for server wide modules")
    all_manifests = get_all_manifests()

    print("Found %s modules" % (len(all_manifests)))

    manifests = {
        filename: get_module(filename)
        for filename in all_manifests
    }

    installable_manifests = {
        filename: module
        for filename, module in manifests.items()
        if is_installable(module)
    }

    print("Found %s installable modules " % (len(installable_manifests),))

    server_wide_modules = get_server_wide_modules(installable_manifests)

    if len(server_wide_modules) > 2:
        modules = ",".join(server_wide_modules)
        print("Setting server wide modules to %s" % (modules))
        config.set('options', 'server_wide_modules', modules)
    else:
        print("No server wide modules found")

    flush_streams()


def setup_environ(config):
    print("Configuring environment variables for postgresql")

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

    # Accpet db_password only with this if some infra cannot be setup
    # otherwise...
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


@contextmanager
def get_config(config_path):
    config = ConfigParser()
    config.read(config_path)

    yield config

    with config_path.open('w') as out:
        config.write(out)


def main():
    # Install apt package first then python packages
    if not os.environ.get('SKIP_SUDO_ENTRYPOINT'):
        ret = call_sudo_entrypoint()
    else:
        ret = 0

    if ret not in [0, None]:
        sys.exit(ret)

    # Install python packages with pip in user home
    valid_paths = get_valid_paths()

    config_path = Path(os.environ.get('ODOO_RC', '/etc/odoo/odoo.cfg'))

    with get_config(config_path) as config:
        if not os.environ.get('SKIP_PIP'):
            install_python_dependencies(valid_paths)
        install_master_password(config)
        setup_environ(config)
        setup_addons_paths(config, valid_paths)
        setup_server_wide_modules(config)

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
