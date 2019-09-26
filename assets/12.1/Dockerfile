FROM llacroix/odoo:12

USER root

RUN pip3 install num2words xlwt xlrd num2words

# Set the default config file
ENV ODOO_RC /etc/odoo/odoo.conf

# Set default user when running the container
USER odoo

ENTRYPOINT ["/entrypoint.sh"]
CMD ["odoo"]
