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

    docker pull llacroix/odoo:12.0-ubuntu

And run with:

    docker run -it llacroix/odoo:12.0-ubuntu

Extra Addons supports
=====================

This image support extra addons in the folder `/addons`. Upon container creation, it will
lookup for requirements.txt file in folders located into `/addons/*` and install them using
`pip` for the current python interpreter.

It will also try to install any deb packages defined in apt-packages.txt file it can find in
the same locations to install debian package available to the ubuntu:bionic distribution.

Warning
=======

This project is still in heavy development, and updating the image may result in breaking
things so consider yourself warned if something stop suddenly working when updating the image.

Until the development gets more stable, consider trying it out in test before pulling new images.
