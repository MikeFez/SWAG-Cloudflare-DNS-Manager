FROM python:3.8-slim-buster

LABEL maintainer="Michael Fessenden <michael@mikefez.com>"

ADD swag_cloudflare_dns_manager /opt/app

ENV DOMAIN=
ENV SUBDOMAINS=
ENV CF_API_EMAIL=
ENV CF_API_KEY=
ENV CF_ZONE_ID=
ENV DDNS_UPDATE_FREQ=

RUN python3 -m venv /opt/app/.venv && \
    /opt/app/.venv/bin/pip install --no-cache-dir -r /opt/app/requirements.txt

ENTRYPOINT ["/bin/sh", "-c", "cd /opt/app && \
            source .venv/bin/activate && \
            python3 app.py"]