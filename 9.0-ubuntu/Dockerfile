FROM ubuntu:18.04
LABEL maintainer="Odoo S.A. <info@odoo.com>"

# Install some deps, lessc and less-plugin-clean-css, and wkhtmltopdf
RUN set -x; \
        apt-get update \
        && apt-get install -y --no-install-recommends \
            ca-certificates \
            curl \
            dirmngr \
            node-less \
            python-gevent \
            python-ldap \
            python-pip \
            python-qrcode \
            python-renderpm \
            # python-support \
            python-vobject \
            python-watchdog \
            python-setuptools \
            python-psycopg2 \
            netcat \
            gnupg \
            apt-utils \
        && curl -o wkhtmltox.deb -sSL https://github.com/wkhtmltopdf/wkhtmltopdf/releases/download/0.12.5/wkhtmltox_0.12.5-1.jessie_amd64.deb \
        && echo '4d104ff338dc2d2083457b3b1e9baab8ddf14202 wkhtmltox.deb' | sha1sum -c - \
        && dpkg --force-depends -i wkhtmltox.deb \
        && apt-get -y install -f --no-install-recommends \
        && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false -o APT::AutoRemove::SuggestsImportant=false npm \
        && rm -rf /var/lib/apt/lists/* wkhtmltox.deb \
        && pip install wheel

RUN set -x; \
       pip install remote-pdb psycogreen

# install latest postgresql-client
RUN set -x; \
        echo 'deb http://apt.postgresql.org/pub/repos/apt/ bionic-pgdg main' > etc/apt/sources.list.d/pgdg.list \
        && export GNUPGHOME="$(mktemp -d)" \
        && repokey='B97B0AFCAA1A47F044F244A07FCC7D46ACCC4CF8' \
        && gpg --batch --keyserver keyserver.ubuntu.com --recv-keys "${repokey}" \
        && gpg --armor --export "${repokey}" | apt-key add - \
        && rm -rf "$GNUPGHOME" \
        && apt-get update  \
        && apt-get install -y postgresql-client libpq-dev \
        && rm -rf /var/lib/apt/lists/*

# Install Odoo
ENV ODOO_VERSION 9.0
ARG ODOO_RELEASE=20190424
RUN set -x; \
        curl -o odoo.tar.gz -sSL https://nightly.odoo.com/${ODOO_VERSION}/nightly/deb/odoo_${ODOO_VERSION}c.${ODOO_RELEASE}.tar.gz \
        && tar xvfz odoo.tar.gz \
        && apt-get update \
        && apt-get install -y python-psutil \
        && cd odoo-${ODOO_RELEASE} \
        && python setup.py install \
        && cd / \
        && rm -rf /odoo-${ODOO_RELEASE}
        # && apt-get -y install -f --no-install-recommends
        # && rm -rf /var/lib/apt/lists/* odoo.deb

RUN useradd -b /var/lib -m odoo
# Copy entrypoint script and Odoo configuration file
COPY ./odoo.conf /etc/odoo/
COPY ./entrypoint.sh /
RUN chown odoo /etc/odoo/odoo

# Expose Odoo services
EXPOSE 8069 8071

# Set the default config file
ENV ODOO_RC /etc/odoo/odoo.conf

# Set default user when running the container
USER odoo

ENTRYPOINT ["/entrypoint.sh"]
CMD ["odoo"]
