FROM ubuntu:bionic
LABEL maintainer="Archeti <info@archeti.ca>"

# Generate locale C.UTF-8 for postgres and general locale data
ENV LANG C.UTF-8

# Install some dependencies python3.7
RUN set -x; \
        apt-get update \
        && apt-get install -y --no-install-recommends \
            python3-wheel \
            python3-setuptools \
            python3-pip \
            python3.7 \
            libpython3.7 \
            curl \
            gnupg \
            libpq-dev \
            libsasl2-2 \
            libldap-2.4-2 \
            sudo \
            node-less \
        && update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.6 1 \
        && update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.7 2 \
        && update-alternatives --install /usr/bin/python python /usr/bin/python3.7 2 \
        && update-alternatives --install /usr/bin/pip pip /usr/bin/pip3 2 \
        && curl -o wkhtmltox.deb -sSL https://github.com/wkhtmltopdf/wkhtmltopdf/releases/download/0.12.5/wkhtmltox_0.12.5-1.bionic_amd64.deb \
        && dpkg --force-depends -i wkhtmltox.deb\
        && apt-get -y install -f --no-install-recommends \
        && rm -rf /var/lib/apt/lists/* wkhtmltox.deb

# Install latest postgresql-client
RUN set -x; \
        echo 'deb https://apt.postgresql.org/pub/repos/apt/ stretch-pgdg main' > etc/apt/sources.list.d/pgdg.list \
        && export GNUPGHOME="$(mktemp -d)" \
        && repokey='B97B0AFCAA1A47F044F244A07FCC7D46ACCC4CF8' \
        && gpg --batch --keyserver keyserver.ubuntu.com --recv-keys "${repokey}" \
        && gpg --armor --export "${repokey}" | apt-key add - \
        && gpgconf --kill all \
        && rm -rf "$GNUPGHOME" \
        && apt-get update  \
        && apt-get install -y postgresql-client \
        && rm -rf /var/lib/apt/lists/*

# Install Odoo Including things from sources
ENV ODOO_VERSION 12.0
ENV ODOO_RELEASE=20191014
ARG ODOO_ARCHIVE=odoo_${ODOO_VERSION}.${ODOO_RELEASE}.tar.gz
RUN set -x; \
        apt-get update \
        && apt-get install -y --no-install-recommends \
            build-essential \
            python3.7-dev \
            libsasl2-dev \
            libldap2-dev  \
        && pip install \
            psycogreen \
            num2words  \
        && pip install https://nightly.odoo.com/${ODOO_VERSION}/nightly/src/${ODOO_ARCHIVE} \
        && cd / \
        && apt-get --purge remove -y \
            build-essential \
            python3.7-dev \
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
    && echo "odoo ALL=(ALL:ALL) NOPASSWD: /sudo-entrypoint.py" >> /etc/sudoers

ENV ODOO_RC /etc/odoo/odoo.conf
ENV ODOO_BASE_PATH /usr/local/lib/python3.7/dist-packages/odoo/addons
# Env variable defined to monitor the kind of service running
# it could be a staging/production/test or anything and undefined
# is the default in case we need to know servers that aren't correctly
# defined
ENV DEPLOYMENT_AREA undefined

expose 8069
expose 8071

USER odoo

ENTRYPOINT ["/entrypoint.py"]

cmd ["odoo"]
