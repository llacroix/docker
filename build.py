#!/usr/bin/env python3
import toml
from datetime import datetime
from os import path
import os
import shutil

FORMAT = "%Y%m%d"

if 'CUR_DATE' in os.environ:
    CUR_DATE = os.environ['CUR_DATE']
else:
    CUR_DATE = datetime.now().strftime(FORMAT)

templates = {}

def get_template(template_name):
    if template_name in templates:
        return templates[template_name]

    template_file = path.join("templates", template_name)

    with open(template_file) as temp_in:
        template = temp_in.read()
        templates[template_name] = template

    return template

with open("./versions.toml") as config_in:
    config = toml.load(config_in)

defaults = config.get('defaults', {})

if path.exists("build"):
    shutil.rmtree("build")

os.mkdir("build")

tags = []

for tag, config in config.get("odoo", {}).items():
    config['tag'] = tag
    config['created_date'] = datetime.now().isoformat()

    config = dict(defaults, **config)

    if 'release' not in config:
        config['release'] = CUR_DATE

    template = get_template(config.get('template'))

    print("Building version tag %s" % tag, config)

    os.mkdir(path.join("build", tag))

    with open(path.join("build", tag, "Dockerfile"), "w") as fout:
        fout.write(template % config)

    shutil.copyfile(path.join("assets", config.get('config')), path.join("build", tag, "odoo.conf"))
    shutil.copyfile(path.join("assets", config.get('entrypoint')), path.join("build", tag, "entrypoint.py"))
    shutil.copyfile(path.join("assets", 'sudo-%s' % config.get('entrypoint')), path.join("build", tag, "sudo-entrypoint.py"))
    os.chmod(path.join("build", tag, "entrypoint.py"), 0o775)
    os.chmod(path.join("build", tag, "sudo-entrypoint.py"), 0o775)

    tags.append(tag)

for tag in tags:
    if path.exists(tag):
        shutil.rmtree(tag)
    shutil.move(path.join("build", tag), ".")

shutil.rmtree("build")
