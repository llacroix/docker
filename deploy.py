import os
from os import path
import shutil
import toml
import tempfile
import argparse
from argparse import ArgumentParser
from contextlib import contextmanager
from datetime import datetime
from subprocess import Popen, PIPE
import select

FORMAT = "%Y%m%d"

if 'CUR_DATE' in os.environ:
    CUR_DATE = os.environ['CUR_DATE']
else:
    CUR_DATE = datetime.now().strftime(FORMAT)


@contextmanager
def cd(dirname):
    current_directory = os.getcwd()
    os.chdir(dirname)
    yield
    os.chdir(current_directory)


def get_parser():
    parser = ArgumentParser("deploy")

    parser.add_argument(
        "-c",
        "--config",
        dest="config",
        type=argparse.FileType('r'),
        help="Configuration file",
        default="versions.toml"
    )

    parser.add_argument(
        '--repository',
        dest="repository",
        help="Repository to push to or in other words the project name",
        default="llacroix/odoo"
    )

    parser.add_argument(
        "-r",
        "--registry",
        dest="registry",
        help="Registry to login to",
        default="index.docker.io",
    )

    parser.add_argument(
        '--verbose',
        dest='verbose',
        action='store_true',
        help="Show more logs",
        default=False
    )

    parser.add_argument(
        '--no-push',
        dest='push',
        action='store_false',
        help="Push to the defined registry",
        default=True
    )

    parser.add_argument(
        '--no-build-image',
        dest='build_image',
        action='store_false',
        default=True,
        help="Prevent building the image"
    )

    parser.add_argument(
        '-o',
        '--output',
        dest='output',
        help="Folder to store the configuration into",
    )

    parser.add_argument(
        '-v',
        '--version',
        dest='versions',
        action='append',
        help="Version to build",
        default=[]
    )

    parser.add_argument(
        '-a',
        '--all',
        dest='all_versions',
        action='store_true',
        help="Build all versions",
        default=False
    )

    parser.add_argument(
        '-s',
        '--save',
        dest='save',
        action='store_true',
        help="Save docker image configuration",
        default=False
    )

    return parser


def get_default(config):
    return config.get('defaults', {})


def get_version(config, version):
    return config.get('odoo', {}).get(version)


def get_config(config, version):
    defaults = get_default(config)
    config = get_version(config, version)

    new_config = defaults.copy()
    new_config.update(config)

    return new_config


def load_template(template_name):
    path = './templates/{}'.format(template_name)
    with open(path, 'r') as template_file:
        return template_file.read()


def load_assets():
    assets = []

    base_path = './assets'
    base_path = path.abspath(base_path)
    for dirname, dirnames, files in os.walk(base_path):
        for file in files:
            file_path = "{}/{}".format(dirname, file)
            stat = os.stat(file_path)
            mode = stat.st_mode & 0o777
            with open(file_path, 'r') as asset_file:
                relpath = path.relpath(file_path, base_path)
                assets.append((
                    relpath, mode, asset_file.read()
                ))

    return assets


def write_assets(assets):
    for file_path, mode, data in assets:
        dir_path = path.dirname(file_path)

        if dir_path:
            os.makedirs(dir_path, exist_ok=True)
        with open(file_path, 'w') as asset_file:
            asset_file.write(data)
        os.chmod(file_path, mode)


def make_dockerfile(odoo_config, template):
    with open("Dockerfile", "w") as fout:
        fout.write(template % odoo_config)


def build_docker_config(args, odoo_config, assets, template, version):
    os.mkdir('build')
    with cd('./build'):
        write_assets(assets)
        make_dockerfile(odoo_config, template)

        if args.build_image:
            build_docker_image(args, odoo_config, version)


def run(params, verbose=False):
    """
    Simple implementation to run some params without blocking
    on big stdout/stderr output.
    """
    process = Popen(params, stdout=PIPE, stderr=PIPE)

    stdout = process.stdout
    stderr = process.stderr

    while True:
        rfd, wfd, xfd = select.select([stdout, stderr], [], [])

        stop_iter = 0

        for fd in rfd:
            try:
                data = next(fd)
                if verbose:
                    print(data.decode(), end="")
            except StopIteration:
                stop_iter += 1

        # When both fd return stopiter then we can conclude
        # both stderr and stdout are closed and wait for
        # the process to finish
        if stop_iter == 2:
            break

    # Wait for the process returncode or status to be defined
    process.wait()

    # return the result
    return process.returncode


def build_docker_image(args, odoo_config, version):
    local_tag = 'local-odoo:{}'.format(version)
    print("Building image {}".format(local_tag))

    build_success = run(
        ['docker', 'build', '-t', local_tag, '.'], args.verbose
    )

    if args.push and build_success == 0:
        remote_tag = '{}/{}:{}'.format(
            args.registry,
            args.repository,
            odoo_config['tag']
        )
        print("Pushing {} to {}".format(local_tag, remote_tag))
        tag_sucess = run(
            ['docker', 'tag', local_tag, remote_tag], args.verbose
        )

        if tag_sucess == 0:
            run(['docker', 'push', remote_tag], args.verbose)


def main():
    parser = get_parser()
    args = parser.parse_args()

    config = toml.load(args.config)

    if args.all_versions:
        versions = config.get('odoo', {}).keys()
    else:
        versions = args.versions

    templates = {}
    assets = load_assets()

    if args.output:
        output_dir = path.abspath(args.output)
    else:
        output_dir = None

    for version in versions:
        odoo_config = get_config(config, version)

        if 'release' not in odoo_config:
            odoo_config['release'] = CUR_DATE

        odoo_config['tag'] = version
        odoo_config['created_date'] = datetime.now().isoformat()

        if odoo_config['template'] not in templates:
            templates[odoo_config['template']] = load_template(
                odoo_config['template']
            )

        template = templates[odoo_config['template']]

        with tempfile.TemporaryDirectory() as directory:
            with cd(directory):
                print(directory)

                build_docker_config(
                    args, odoo_config, assets, template, version
                )

                if args.output:
                    project_path = path.join(output_dir, version)
                    build_path = path.join(directory, 'build')

                    print("Moving build path {} to {}".format(
                        build_path, project_path
                    ))

                    if path.exists(project_path):
                        shutil.rmtree(project_path)

                    shutil.move(build_path, project_path)


if __name__ == '__main__':
    main()
