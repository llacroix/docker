FROM ubuntu:bionic
LABEL maintainer="Archeti <info@archeti.ca>"

# Generate locale C.UTF-8 for postgres and general locale data
ENV LANG C.UTF-8
ARG DEBIAN_FRONTEND=noninteractive

# Install some dependencies python3.7
RUN set -x; \
        apt-get update \
        && apt-get install -y --no-install-recommends \
            python3-wheel \
            python3-setuptools \
            python3-pip \
            # python3.7 \
            # libpython3.7 \
            curl \
            gnupg \
            libpq-dev \
            libsasl2-2 \
            libldap-2.4-2 \
            libxml2 \
            libxmlsec1 \
            libxslt1.1 \
            sudo \
            node-less \
            # python3-yaml \
        && update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.6 1 \
        # && update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.7 2 \
        && update-alternatives --install /usr/bin/python python /usr/bin/python3.6 1 \
        && update-alternatives --install /usr/bin/pip pip /usr/bin/pip3 2 \
        && curl -o wkhtmltox.deb -sSL https://github.com/wkhtmltopdf/wkhtmltopdf/releases/download/0.12.5/wkhtmltox_0.12.5-1.bionic_amd64.deb \
        && apt-get install -y --no-install-recommends ./wkhtmltox.deb \
        && rm -rf /var/lib/apt/lists/* wkhtmltox.deb

# Install latest postgresql-client
RUN set -x; \
        echo 'deb https://apt.postgresql.org/pub/repos/apt/ bionic-pgdg main' > etc/apt/sources.list.d/pgdg.list \
        && export GNUPGHOME="$(mktemp -d)" \
        && repokey='B97B0AFCAA1A47F044F244A07FCC7D46ACCC4CF8' \
        && gpg --batch --keyserver keyserver.ubuntu.com --recv-keys "${repokey}" \
        && gpg --batch --armor --export "${repokey}" > /etc/apt/trusted.gpg.d/pgdg.gpg.asc \
        && gpgconf --kill all \
        && rm -rf "$GNUPGHOME" \
        && apt-get update  \
        && apt-get install -y postgresql-client \
        && rm -rf /var/lib/apt/lists/*

ENV PATH=/usr/local/bin:$PATH
# Install Odoo Including things from sources
ENV ODOO_VERSION 11.0
ENV ODOO_RELEASE=20200623
ARG ODOO_ARCHIVE=odoo_${ODOO_VERSION}.${ODOO_RELEASE}.tar.gz
RUN set -x; \
        apt-get update \
        && apt-get install -y --no-install-recommends \
            build-essential \
            python3.6-dev \
            libsasl2-dev \
            libldap2-dev ruby-sass \
            libxml2-dev \
            libxmlsec1-dev \
            libxslt1-dev \
        && pip install -U pip \
        && /usr/bin/env pip install \
            psycogreen \
             \
        && curl -o requirements.txt https://raw.githubusercontent.com/odoo/odoo/${ODOO_VERSION}/requirements.txt \
        && pip install -r requirements.txt \
        && /usr/bin/env pip install https://nightly.odoo.com/${ODOO_VERSION}/nightly/src/${ODOO_ARCHIVE} \
        && cd / \
        && apt-get --purge remove -y \
            build-essential \
            python3.6-dev \
            libsasl2-dev \
            libldap2-dev \
            libxml2-dev \
            libxmlsec1-dev \
            libxslt1-dev \
        && apt-get autoremove -y \
        && rm -rf /var/lib/apt/lists/*

VOLUME /etc/odoo
VOLUME /var/lib/odoo

COPY ./odoo.conf /etc/odoo/
COPY ./entrypoint.py /
COPY ./sudo-entrypoint.py /
COPY ./find_modules.py /scripts/find_modules.py
COPY ./prepare_project.py /scripts/prepare_project.py

ARG UID=1000
ARG GID=1000

RUN mkdir /addons \
    && groupadd -r -g ${GID} odoo \
    && useradd -r -u ${UID} -g odoo -b /var/lib -m odoo \
    && chown odoo /etc/odoo/odoo.conf \
    && chown -R odoo:odoo /addons \
    && echo "odoo ALL=(ALL:ALL) NOPASSWD:SETENV: /sudo-entrypoint.py" >> /etc/sudoers

ENV ODOO_RC /etc/odoo/odoo.conf
ENV ODOO_BASE_PATH /usr/local/lib/python3.6/dist-packages/odoo/addons
# Env variable defined to monitor the kind of service running
# it could be a staging/production/test or anything and undefined
# is the default in case we need to know servers that aren't correctly
# defined
ENV DEPLOYMENT_AREA undefined

expose 8069
expose 8071

USER odoo

LABEL version="11.0"
LABEL release="20200623"

LABEL org.opencontainers.image.created="2021-06-25T17:55:41.194840"
LABEL org.opencontainers.image.url="https://hub.docker.com/r/llacroix/odoo"
LABEL org.opencontainers.image.authors="Archeti <info@archeti.ca>"
LABEL org.opencontainers.image.documentation="https://github.com/llacroix/odoo-docker"
LABEL org.opencontainers.image.source="https://github.com/llacroix/odoo-docker"
LABEL org.opencontainers.image.version="11.0"
LABEL org.opencontainers.image.vendor="ArcheTI"
LABEL org.opencontainers.image.ref.name="11.0"
LABEL org.opencontainers.image.title="Odoo 11.0"
LABEL org.opencontainers.image.description="Full featured odoo image that make odoo deployment fun and secure."

ENTRYPOINT ["/entrypoint.py"]

cmd ["odoo"]
