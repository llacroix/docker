FROM ubuntu:bionic
LABEL maintainer="Archeti <info@archeti.ca>"

# Generate locale C.UTF-8 for postgres and general locale data
ENV LANG C.UTF-8
ARG DEBIAN_FRONTEND=noninteractive

COPY ./platform.sh /platform.sh
# Install some dependencies python3.7
RUN set -x; \
        export ARCH=`sh /platform.sh` \
        # Setup deb source for postgresql client
        && apt-get update \
        && apt-get install -y --no-install-recommends \
            ca-certificates \
            gnupg \
            python-wheel \
            python-setuptools \
            python-pip \
            python2.7 \
            libpython2.7 \
            curl \
            libpq-dev \
            libsasl2-2 \
            libldap-2.4-2 \
            libxml2 \
            libxmlsec1 \
            libxslt1.1 \
            sudo \
            node-less \
        && echo 'deb https://apt.postgresql.org/pub/repos/apt/ bionic-pgdg main' > etc/apt/sources.list.d/pgdg.list \
          && export GNUPGHOME="$(mktemp -d)" \
          && repokey='B97B0AFCAA1A47F044F244A07FCC7D46ACCC4CF8' \
          && gpg --batch --keyserver keyserver.ubuntu.com --recv-keys "${repokey}" \
          && gpg --batch --armor --export "${repokey}" > /etc/apt/trusted.gpg.d/pgdg.gpg.asc \
          && gpgconf --kill all \
          && rm -rf "$GNUPGHOME" \
        # Download deb for wkhtmltox
        && echo "Downloading https://github.com/wkhtmltopdf/wkhtmltopdf/releases/download/0.12.5/wkhtmltox_0.12.5-1.bionic_${ARCH}.deb" \
          && curl -o wkhtmltox.deb -sSL https://github.com/wkhtmltopdf/wkhtmltopdf/releases/download/0.12.5/wkhtmltox_0.12.5-1.bionic_${ARCH}.deb \
        && apt-get update \
        && apt-get install -y --no-install-recommends \
            postgresql-client \
            ./wkhtmltox.deb \
        && rm -rf /var/lib/apt/lists/* wkhtmltox.deb

ENV PATH=/var/lib/odoo/.local/bin:/usr/local/bin:$PATH
# Install Odoo Including things from sources
ENV ODOO_VERSION 8.0
ENV ODOO_RELEASE=20171001
ARG ODOO_ARCHIVE=odoo_${ODOO_VERSION}.${ODOO_RELEASE}.tar.gz
RUN set -x; \
        apt-get update \
        && apt-get install -y --no-install-recommends \
            build-essential \
            python2.7-dev \
            libsasl2-dev \
            libldap2-dev  \
            libxml2-dev \
            libxmlsec1-dev \
            libxslt1-dev \
            git \
        && pip install -U pip \
        && /usr/bin/env pip install \
            odoo-tools==0.0.65 \ 
            pathlib2 \
        && odoo-install --release "20171001" --version "8.0" --repo "https://github.com/odoo/odoo.git" --ref "" \
        && [ -f /usr/local/bin/odoo.py ] && ln -s /usr/local/bin/odoo.py /usr/local/bin/odoo \
        || cd / \
        && apt-get --purge remove -y \
            build-essential \
            python2.7-dev \
            libsasl2-dev \
            libldap2-dev \
            libxml2-dev \
            libxmlsec1-dev \
            libxslt1-dev \
            git \
        && apt-get autoremove -y \
        && rm -rf /var/lib/apt/lists/* \
        && rm -rf /root/.cache

COPY ./odoo.conf /etc/odoo/
COPY ./entrypoint.py /
COPY ./sudo-entrypoint.py /

ARG UID=1000
ARG GID=1000

RUN mkdir /addons \
    && groupadd -r -g ${GID} odoo \
    && useradd -r -u ${UID} -g odoo -b /var/lib -m odoo \
    && chown odoo /etc/odoo/odoo.conf \
    && chown -R odoo:odoo /addons \
    && echo "odoo ALL=(ALL:ALL) NOPASSWD:SETENV: /sudo-entrypoint.py" >> /etc/sudoers

VOLUME /etc/odoo
VOLUME /var/lib/odoo

ENV ODOO_RC /etc/odoo/odoo.conf
ENV ODOO_BASE_PATH /usr/local/lib/python2.7/dist-packages/openerp/addons
# Env variable defined to monitor the kind of service running
# it could be a staging/production/test or anything and undefined
# is the default in case we need to know servers that aren't correctly
# defined
ENV DEPLOYMENT_AREA undefined

expose 8069
expose 8071

USER odoo

LABEL version="8.0"
LABEL release="20171001"

LABEL org.opencontainers.image.created="2022-11-04T20:06:13.797586"
LABEL org.opencontainers.image.url="https://hub.docker.com/r/llacroix/odoo"
LABEL org.opencontainers.image.authors="OdooPlus <info@odoo.plus>"
LABEL org.opencontainers.image.documentation="https://github.com/llacroix/odoo-docker"
LABEL org.opencontainers.image.source="https://github.com/llacroix/odoo-docker"
LABEL org.opencontainers.image.version="8.0"
LABEL org.opencontainers.image.vendor="OdooPlus"
LABEL org.opencontainers.image.ref.name="8.0"
LABEL org.opencontainers.image.title="Odoo 8.0"
LABEL org.opencontainers.image.description="Full featured odoo image that make odoo deployment fun and secure."

ENTRYPOINT ["/entrypoint.py"]

cmd ["odoo"]
