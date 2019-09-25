#!/usr/bin/env python3
import argparse
import time
import os
import shlex
import subprocess
import sys
import glob
import pip

package_list = set()

def pipe(args):
    process = subprocess.Popen(
        args,
        stdin=sys.stdin,
        stdout=sys.stdout,
        stderr=sys.stderr,
    )

    process.wait()

    return process.returncode

for packages in glob.glob("/addons/**/apt-packages.txt"):
    print("Installing packages from %s" % packages)
    with open(packages, 'r') as pack_file:
        lines = [line.strip() for line in pack_file]         
        package_list.update(set(lines))
    
    ret = pipe(['apt-get', 'update'])

    if ret != 0:
        sys.exit(ret)

    ret = pipe(['apt-get', 'install', '-y'] + list(package_list))

    if ret != 0:
        sys.exit(ret)

for requirements in glob.glob("/addons/**/requirements.txt"):
    print("Installing python packages from %s" % requirements)
    pip.main(['install', '-r', requirements])

quoted_args = [
    shlex.quote(arg)
    for arg in sys.argv[1:]
] or ["true"]

username = "odoo"

# Run the command as odoo while everything is quoted
ret = pipe(["su", username, "-c", " ".join(quoted_args)])

sys.exit(ret)
