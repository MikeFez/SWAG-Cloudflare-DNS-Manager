FROM python:3.8

LABEL maintainer="Michael Fessenden <michael@mikefez.com>"

ADD swag_cloudflare_dns_manager /opt/app

ENV USERNAME=dev
ENV PUID=1000
ENV PGID=1000

ENV DOMAIN=
ENV SUBDOMAINS=
ENV CF_API_EMAIL=
ENV CF_API_KEY=
ENV CF_ZONE_ID=
ENV DDNS_UPDATE_FREQ=

RUN groupadd -g ${PGID} ${USERNAME} \
    && useradd -u ${PUID} -g ${USERNAME} -d /home/${USERNAME} ${USERNAME} \
    && mkdir /home/${USERNAME} \
    && chown -R ${USERNAME}:${USERNAME} /home/${USERNAME}

RUN cd /opt/app && \
    python3 -m venv .venv && \
    source .venv/bin/activate && \
    pip3 install --no-cache-dir -r requirements.txt

ENTRYPOINT ["/bin/sh", "-c", \
            "cd /opt/app && \
            source .venv/bin/activate && \
            python3 app.py"]