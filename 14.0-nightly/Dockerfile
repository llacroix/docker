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
            sudo \
            node-less \
            python3-yaml \
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
ENV ODOO_VERSION 14.0
ENV ODOO_RELEASE=20200106
ARG ODOO_ARCHIVE=odoo_14.0alpha1.${ODOO_RELEASE}.tar.gz
RUN set -x; \
        apt-get update \
        && apt-get install -y --no-install-recommends \
            build-essential \
            python3.6-dev \
            libsasl2-dev \
            libldap2-dev python3-babel python3-chardet python3-dateutil python3-decorator python3-docutils python3-feedparser python3-html2text python3-pil python3-jinja2 python3-libsass python3-lxml python3-mako python3-mock python3-passlib python3-polib  python3-psutil python3-psycopg2 python3-pydot python3-pyparsing python3-pypdf2 python3-qrcode python3-reportlab python3-requests python3-suds python3-tz python3-vatnumber python3-vobject python3-werkzeug python3-xlsxwriter python3-xlrd python3-pyldap \
        && pip install -U pip \
        && /usr/bin/env pip install \
            psycogreen \
            num2words  \
        && /usr/bin/env pip install https://nightly.odoo.com/master/nightly/src/${ODOO_ARCHIVE} \
        && cd / \
        && apt-get --purge remove -y \
            build-essential \
            python3.6-dev \
            libsasl2-dev \
            libldap2-dev \
        && apt-get autoremove -y \
        && rm -rf /var/lib/apt/lists/*

VOLUME /etc/odoo
VOLUME /var/lib/odoo

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

LABEL version="14.0"
LABEL release="20200106"

LABEL org.opencontainers.image.created="2020-01-06T23:00:06.448148"
LABEL org.opencontainers.image.url="https://hub.docker.com/r/llacroix/odoo"
LABEL org.opencontainers.image.authors="Archeti <info@archeti.ca>"
LABEL org.opencontainers.image.documentation="https://github.com/llacroix/odoo-docker"
LABEL org.opencontainers.image.source="https://github.com/llacroix/odoo-docker"
LABEL org.opencontainers.image.version="14.0"
LABEL org.opencontainers.image.vendor="ArcheTI"
LABEL org.opencontainers.image.ref.name="14.0-nightly"
LABEL org.opencontainers.image.title="Odoo 14.0"
LABEL org.opencontainers.image.description="Full featured odoo image that make odoo deployment fun and secure."

ENTRYPOINT ["/entrypoint.py"]

cmd ["odoo"]
