from optparse import OptionParser
from pathlib import Path
import toml
from giturlparse import parse
from contextlib import contextmanager
import os
from subprocess import run
from urllib.parse import urlparse


def get_services(services):
    return {
        service.get('name'): service
        for service in services.get('services')
    }


def addons_by_project(options, addons):
    res = {}

    for addon in addons:
        if addon['url'] == 'self':
            if options.ignore_self:
                continue
            parsed = parse(options.url)
        else:
            parsed = parse(addon['url'])

        auth = parsed.protocol in ['git', 'ssh']

        res[parsed.repo] = dict(
            addon,
            url=parsed.url2https,
            auth=auth
        )

    return res


def merge_addons(options, base, other):
    base_addons = addons_by_project(options, base)
    other_addons = addons_by_project(options, other)

    for name, addon in other_addons.items():
        if name not in base_addons:
            base_addons[name] = addon
        else:
            base_addons[name] = dict(base_addons[name], **addon)

    return [
        addon
        for addon in base_addons.values()
    ]


def merge_services(options, base, other):
    basic_inherit = dict(base, **other)

    if base.get('addons') or other.get('addons'):
        basic_inherit['addons'] = merge_addons(
            options,
            base.get('addons', []),
            other.get('addons', [])
        )

    return basic_inherit


def compile_service(options, services, name):
    service = services.get(name, {})
    if 'inherit' in service:
        merge_service = compile_service(options, services, service['inherit'])
        service = merge_services(options, merge_service, service)

    return service


def get_parser():
    parser = OptionParser()

    parser.add_option(
        '-f',
        '--file',
        dest="file",
        help="Input File"
    )

    parser.add_option(
        '--url',
        dest='url',
        help="Url of self project"
    )

    parser.add_option(
        '-o',
        '--output',
        dest="output_directory",
        help="Output Directory"
    )

    parser.add_option(
        '-e',
        dest="env",
        help="Environment to prepare"
    )

    parser.add_option(
        '--username',
        dest="username",
        help="Username to replace with",
    )

    parser.add_option(
        '--password',
        dest="password",
        help="password to set on https urls"
    )

    parser.add_option(
        '-b',
        '--branch',
        dest="branch",
        help="Default branch if no ref is defined"
    )

    parser.add_option(
        '--ignore-self',
        dest="ignore_self",
        action="store_true",
        help="Ignore self url as it's already fetched",
        default=False
    )

    return parser


@contextmanager
def cd(directory):
    cwd = Path.cwd()
    try:
        os.chdir(directory)
        yield
    finally:
        os.chdir(cwd)


def fetch_addons(options, addon):
    parsed = parse(addon['url'])

    url = urlparse(parsed.url2https)

    if addon['auth'] and options.username and options.password:
        url = url._replace(
            netloc="{}:{}@{}".format(
                options.username,
                options.password,
                url.netloc
            )
        )

    repo_path = Path.cwd() / options.output_directory / parsed.repo

    repo_path.mkdir(exist_ok=True)

    with cd(repo_path):
        run(['git', 'init'])
        run(['git', 'remote', 'add', 'origin', url.geturl()])

        ref = addon.get('commit') or addon.get('branch') or options.branch

        if ref:
            run(['git', 'fetch', 'origin', ref])
        else:
            run(['git', 'fetch', 'origin'])

        run(['git', 'checkout', 'FETCH_HEAD'])
        run(['git', 'remote', 'remove', 'origin'])


def main(options, args):
    with Path(options.file).open('r') as fin:
        services = toml.loads(fin.read())

    by_name = get_services(services)

    outputdir = Path(options.output_directory)
    outputdir.mkdir(exist_ok=True)

    service = compile_service(options, by_name, options.env)

    for addons in service.get('addons', []):
        fetch_addons(options, addons)


if __name__ == '__main__':
    parser = get_parser()
    (options, args) = parser.parse_args()
    main(options, args)
