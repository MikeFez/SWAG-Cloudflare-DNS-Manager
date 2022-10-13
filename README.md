# SWAG-Cloudflare-DNS-Manager
Synchronize DNS records (and manage Dynamic DNS) within Cloudflare for items managed by SWAG.

## What is this?
[SWAG](https://github.com/linuxserver/docker-swag) (Secure Web Application Gateway) sets up a Nginx webserver and reverse proxy with php support and a built-in certbot client that automates free SSL server certificate generation and renewal processes (Let's Encrypt and ZeroSSL). It also contains fail2ban for intrusion prevention.

Basically, SWAG allows you to point requests for specific subdomains to assigned containers, without the need to expose ports.

For added protection to my self-hosted services, I proxy all requests through Cloudflare. This adds an extra layer of security by not exposing my home IP, as well as allows for firewall rules to help prevent access from malicious parties. However, wildcard subdomain redirects cannot be proxied, and require each subdomain to be specifically defined. This means that the added protection Cloudflare offers will not be enabled unless individual DNS Type A records are generated for each subdomain that SWAG manages.

**This container automates the creation of DNS records within Cloudflare for each subdomain managed by SWAG. It also provides Dynamic DNS for monitored DNS records, updating the IP address they point to should the public IP of the network the container is running changes.**

What does this mean? When SWAG is updated with a new subdomain entry, this container will generate the applicable Cloudflare DNS record for you!

## Usage
DNS records are only created upon container startup. It is suggested provide your domain and list of subdomains to both `SWAG` and `swag-cloudflare-dns-manager` as env variables within a `.env` file. Doing so ensures that should the domain or list of subdomains change, both containers are rebuilt upon `docker-compose up`, synchronizing them.

### docker-compose (recommended, [click here for more info](https://docs.linuxserver.io/general/docker-compose))

```yaml
---
version: "2.1"
services:
  swag: # Configuration options found here: https://docs.linuxserver.io/images/docker-swag
    image: ghcr.io/linuxserver/swag:latest
    container_name: swag
    cap_add:
      - NET_ADMIN
    ports:
      - 80
      - 443
    volumes:
      - ${DOCKER_VOLUMES_DIR}/swag:/config
    environment:
      - PGID
      - PUID
      - TZ
      - EMAIL=${MY_EMAIL}
      - URL=${DOMAIN}
      - SUBDOMAINS
      - VALIDATION=dns
      - DNSPLUGIN=cloudflare
    restart: unless-stopped

  swag-cloudflare-dns-manager:
    image: ghcr.io/mikefez/swag-cloudflare-dns-manager:main
    container_name: swag-cloudflare-dns-manager
    environment:
      - DOMAIN  # Base domain
      - PROXIED_RECORDS=${SUBDOMAINS},extra-subdomain   # These items will be proxied. Should you want to manage subdomains which are not provided to SWAG, you can extend this list by appending comma-separated subdomains. Items in this list which are also provided to UNPROXIED_RECORDS will be unproxied.
      - UNPROXIED_RECORDS=plex,ssh  # These items will not be proxied. Plex requires port 32400 which cloudflare does not provide, and my SSH port is not the default.
      - CF_API_EMAIL=${MY_EMAIL}
      - CF_API_KEY
      - CF_ZONE_ID
      - DDNS_UPDATE_FREQ=1800  # Check DDNS every 30 minutes.
    restart: unless-stopped
```

## Parameters

Container images are configured using parameters passed at runtime (such as those above). These parameters are separated by a colon and indicate `<external>:<internal>` respectively. For example, `-p 8080:80` would expose port `80` from inside the container to be accessible from the host's IP on port `8080` outside the container.

| Parameter | Function |
| :----: | --- |
| `-e DOMAIN` | Base domain for which DNS records should be managed. For example, a DNS record for `subdomain.example.com` requires this value to be `example.com`. For multi level subdomains such as  `sub2.sub1.example.com`, this value should be `sub1.example.com`. |
| `-e PROXIED_RECORDS` | Comma-separated list of subdomains which should be proxied. |
| `-e UNPROXIED_RECORDS` | Comma-separated list of subdomains which should not be proxied (such as items that need [non-approved port](https://support.cloudflare.com/hc/en-us/articles/200169156-Identifying-network-ports-compatible-with-Cloudflare-s-proxy) access). If an subdomain is provided to both `PROXIED_RECORDS` and `UNPROXIED_RECORDS`, it will end up unproxied. This allows users to easily proxy the entirety of subdomains which SWAG handles, with the option to override specific items here. |
| `-e CF_API_EMAIL` | Cloudflare email address. |
| `-e CF_API_KEY` | Cloudflare API key. |
| `-e CF_ZONE_ID` | ZoneID for the property to manage. |
| `-e DDNS_UPDATE_FREQ=1800` | Frequency to check DDNS. Updates only occur if there has been an IP change. |

## ToDo
- Add debug mode that prevents actual actions from occurring
