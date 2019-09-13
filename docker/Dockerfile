FROM python:3.7-slim-buster

RUN	apt-get update && \
    apt-get install -y --no-install-recommends graphviz gosu && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

COPY server/requirements.txt /tmp/
RUN pip install --no-cache-dir -r /tmp/requirements.txt

RUN useradd --create-home ntg
WORKDIR /home/ntg

COPY .pgpass                /home/ntg/

RUN chown ntg:ntg .pgpass && chmod 600 .pgpass

COPY server                 /home/ntg/server
COPY ntg_common             /home/ntg/ntg_common
COPY *.conf                 /home/ntg/instance/
COPY client                 /home/ntg/client
COPY api.conf.js            /home/ntg/client
COPY scripts/*.py           /home/ntg/scripts/

COPY docker-entrypoint.sh   /usr/local/bin/

EXPOSE 5000

ENV PYTHONPATH /home/ntg:/home/ntg/server

USER ntg

ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["app-server"]
