from optparse import OptionParser
from pathlib import Path
from itertools import chain


def get_parser():
    parser = OptionParser()

    parser.add_option(
        "-p",
        dest='paths',
        action="append",
        help="Location in which to search",
        default=[]
    )

    parser.add_option(
        "--only-name",
        dest="only_name",
        action="store_true",
        help="Only display module name instead of path",
        default=False,
    )

    parser.add_option(
        '--csv',
        dest="is_csv",
        action="store_true",
        help="Output as a comma separated list",
        default=False
    )

    return parser


def find_modules(options, path):
    modules = set()

    path = Path.cwd() / path

    erp_manifest = '__openerp__.py'
    odoo_manifest = '__manifest__.py'

    manifest_globs = chain(
        path.glob('**/{}'.format(erp_manifest)),
        path.glob('**/{}'.format(odoo_manifest)),
    )

    for path in manifest_globs:
        rel_path = path.parent.relative_to(Path.cwd())
        if options.only_name:
            modules.add(rel_path.name)
        else:
            modules.add(str(rel_path))

    return modules


def main(options, args):
    modules = set()
    for path in options.paths:
        modules = modules.union(find_modules(options, path))

    return modules


if __name__ == '__main__':
    parser = get_parser()
    (options, args) = parser.parse_args()
    modules = main(options, args)

    if not options.is_csv:
        for module in modules:
            print(module)
    else:
        print(",".join(modules), end="")
