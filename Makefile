build:
	docker build \
		--tag swag_cloudflare_dns_manager:latest \
		.

run:
	docker run \
		--rm \
		-it \
		-e DOMAIN=$(DOMAIN) \
		-e SUBDOMAINS=$(SUBDOMAINS) \
		-e UNPROXIED_SUBDOMAINS=$(UNPROXIED_SUBDOMAINS) \
		-e CF_API_EMAIL=$(CF_API_EMAIL) \
		-e CF_API_KEY=$(CF_API_KEY) \
		-e CF_ZONE_ID=$(CF_ZONE_ID) \
		-e DDNS_UPDATE_FREQ=$(DDNS_UPDATE_FREQ) \
		--name swag_cloudflare_dns_manager \
		swag_cloudflare_dns_manager:latest
