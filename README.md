About this repo
===============

This is a fork of the original odoo docker repository. This project bring a lot of new
improvements such as a more uniform configuration for all odoo projects.

It tries to support version from 8.0 to the latest versions of odoo. The recent changes
added a script to generate the Docker files with templating to support python2 and python3
odoo.

How to use
==========

pull the images with the following command for odoo 12.0:

    docker pull llacroix/odoo:13

And run with:

    docker run -it llacroix/odoo:13 odoo --db_host [db_host]


To run with addons, you can use it like this:

    docker run -it -v /path_to/some_addons:/addons/some_addons llacroix/odoo:13 --db_host [db_host]


Supported environment variables
===============================

NAME                      | Definition
------------------------- | ------------------------------------
`PGHOST`                  | Postgres hostname/ip.
`PGUSER`                  | Postgres user for connection.
`PGDATABASE`              | Database to connect to.
`PGPASSWORD`              | Password to use but only working when paired with `I_KNOW_WHAT_IM_DOING=TRUE`.
`I_KNOW_WHAT_IM_DOING`    | A trigger required to enable dangerous configurations.
`PGRETRY`                 | Amount of times to retry connections.
`PGRETRYTIME`             | Amount of times to wait between connections retry.
`ODOO_SKIP_POSTGRES_WAIT` | Skip waiting for postgres.
`ODOO_RC`                 | Path to odoo config file.
`MASTER_PASSWORD`         | Master Pasword to be defined.
`DEPLOYMENT_AREA`         | Defined to know in which area is the container deployed.
`ODOO_VERSION`            | Odoo version as defined in the image for example: 13.0
`ODOO_RELEASE`            | Odoo release as defined in the image for example: 20191020
`ODOO_BASE_PATH`          | Base path for odoo addons installed by pip.
`ODOO_DISABLED_MODULES`   | Comma separated list of core odoo modules to remove from path. This is useful when you have customization made to core modules inside your personal addons path.
`RESET_ACCESS_RIGHTS`     | Set to TRUE to reset access rights on startup. It is disabled by default due to how slow it can be.
`ODOO_EXTRA_PATHS`        | Comma separated list of paths to include that aren't in /addons
`ODOO_EXCLUDED_PATHS`     | Comma separated list of paths to exclude from the entrypoint. It will exclude the path itself and children.
                                       
    

Features:
=========

Load PG variables and wait for connection
-----------------------------------------

Environment variables are set from ODOORC file and or from command line arguments.
If env variables are available it will also use them to setup ENV variables for
postgres.

Before starting odoo, a connection to postgres is attempted with the defined
env variables. The connection string for psycopg2 is emtpy in order to use the
default values available and also make use of .pgpass file available in the
environment. This way, it is possible to connect to postgres without explicitely
pass a password in cleartext anywhere.

The .pgpass file should be enough to connect to the database without setting 
an env variable named PGPASSWORD or using `--db_password`. This image doesn't
support storing password in cleartext or as a parameter so `--db_password` will
have no effect on the connection retry unless you pass the env variable:

    I_KNOW_WHAT_IM_DOING=TRUE

In the environment.

Automatic MasterPassword Generation
-----------------------------------

By default, odoo open the web manager to anyone by not setting a master password. This can
be dangerous in a way that a new instance is opening your database to everyone by default.
For that reason, the entrypoint of this image will define a default password if none is
provided.

MasterPassword through secrets
------------------------------

It's possible to set a master password using docker swarm secrets. When the instance boots,
odoo check for a `master_password` file in the secrets folder and extract its content as the
value of the password. If the password is not encrypted, it will automatically encrypt it
and save it into the `ODOO_RC` file path. Encryption is only supported by version of odoo higher
than 10 because encryption wasn't supported with version prior. 

Extra Addons supports
---------------------

This image support extra addons in the folder `/addons`. Upon container creation, it will
lookup for requirements.txt file in folders located into `/addons/*` and install them using
`pip` for the current python interpreter.

It will also try to install any deb packages defined in apt-packages.txt file it can find in
the same locations to install debian package available to the ubuntu:bionic distribution.


Server Wide Modules
-------------------

In order to define server wide modules, an extension is used in the manifest by defining the
property `"server_wide": True`. This will allow odoo to automatically load some modules as
server wide. This is unfortunately not perfect as some modules should not be in the path
of addons unless you want to use them. Server Wide modules don't have to be installed and
having a server wide module is similar as loading it while not installing it by default.

That feature should be used at your own risk and might be disabled by default in the future
in order to prevent some "bad" players to abuse the `server_wide` attribute if it was
to become more popular.

Ideally, modules should be staged in folders that let you install them while keeping them out
of the `addons_path`. Odoo should be able to introspect and move them into the addons path...

Yet in a multi-database setup, this makes little sense as each instance may or may not want
to have some server wide modules available. 

Warning
=======

This project is still in heavy development, and updating the image may result in breaking
things so consider yourself warned if something stop suddenly working when updating the image.

Until the development gets more stable, consider trying it out in test before pulling new images.


How to build new images:
========================

Run the script `deploy.py` to generate the Dockerfile based on the versions.toml file.


For example to rebuild all configurations in the current folder without rebuilding images.

    python deploy.py --verbose --no-push --no-build-image -a -o .


In order to push to a registry you have to pass a registry and a repository. The following
command line will generate the configurations in current folder and push them to the registry
for each versions defined in `versions.toml`.

   python deploy.py --verbose --registry index.docker.io --repository llacroix/odoo -a -o . 


If you need to deploy a specific version of an image you can pass the `-v` parameter. And `--no-push`
without `--no-build-image` would build the image with the tag `local-odoo:14.0` in this particular case.

   python deploy.py --versbose --no-push -v 14.0 -o .


TODO:
=====

- [x] Added stable images based on older version of odoo and nightly tag for odoo release updated
      daily. This can be useful to have around a week to test that updating the stable image will
      not create unforseen behaviour.
- [x] Wait for postgres to be up and available for connection to prevent odoo from hanging in limbo
- [x] Uniform setup for odoo 8 to 13, make odoo work transparently regardless of the openerp 
      name for versions with openerp instead of odoo.
- [x] Run entrypoint as odoo user with a sudo entrypoint that remove itself from sudoers when 
      done with pre configuration process.
- [x] Add some way to expose deployment area/zone which can be used later for monitoring the odoo
      servers based on their deployment status.. canari/staging/production/tests etc
- [x] Define Postgres Environment variable to make it easier to connect to postgres from within the
      container.
- [x] Use a secret to setup a `.pgpass` file for postgres
- [x] Fix dependencies for ubuntu bionic
- [x] Automatically build addons path parameters based on folders in `/addons/*` and environment 
      variables.
- [x] Improve labels to conform with https://github.com/opencontainers/image-spec/blob/master/annotations.md
- [x] -Automatically detect modules that should get update on boot. For example, you want to start
      odoo and always update a certain set of modules or a certain set of addons repository.-
      This shouldn't be handled by this project.
- [x] Automatically detect server wide modules
- [x] Refactor the deploy/build script in an unified script
- [x] Remove Dockerfiles for a continuous integration script. Dockerfile should be automatically generated
      then have image built by CI then pushed to different registry.
