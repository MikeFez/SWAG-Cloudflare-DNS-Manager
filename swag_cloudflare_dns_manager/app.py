from include import cloudflare
import logging
from time import sleep
import os

logging.basicConfig(level=logging.INFO)

DOMAIN = os.getenv("DOMAIN", default = None)
SUBDOMAINS = os.getenv("SUBDOMAINS", default = None)
UNPROXIED_SUBDOMAINS = os.getenv("UNPROXIED_SUBDOMAINS", default = None)
DDNS_UPDATE_FREQ = os.getenv("DDNS_UPDATE_FREQ", default = None)
missing_env_vars = [v for v in (DOMAIN, SUBDOMAINS, DDNS_UPDATE_FREQ) if v is None]
if missing_env_vars:
    raise Exception(f"Missing env vars: {missing_env_vars}")

ACTUAL_SUBDOMAINS = [f"{sub}.{DOMAIN}" for sub in SUBDOMAINS.split(",") + ["www"]] + [DOMAIN]
ACTUAL_UNPROXIED_SUBDOMAINS = [f"{sub}.{DOMAIN}" for sub in UNPROXIED_SUBDOMAINS.split(",")] if UNPROXIED_SUBDOMAINS is not None else []

def set_dns():
    current_ip = cloudflare.get_current_ip()
    records_by_name = [rec.name for rec in cloudflare.get_records()]

    domains_by_proxy = {
        True: ACTUAL_SUBDOMAINS,
        False: ACTUAL_UNPROXIED_SUBDOMAINS
    }
    # Discover new
    records_added = 0
    for proxy_enabled, subdomain in domains_by_proxy.items():
        if subdomain not in records_by_name:
            logging.info(f"Creating DNS Record for {subdomain}")
            cloudflare.create_record(cloudflare.DNSRecord(dns_name=subdomain,
                                                          dns_ip=current_ip,
                                                          dns_proxied=proxy_enabled))
            logging.info(f"\t{subdomain} has been created.")
            record_added += 1
    if records_added > 0:
        logging.info(f"Added {records_added} new DNS record{'s' if records_added > 0 else ''}")
    else:
        logging.info("No DNS records needed to be added")


def ddns_loop():
    while True:
        try:
            logging.info("Checking For DDNS Updates")
            current_ip = cloudflare.get_current_ip()
            for dns_record in cloudflare.get_records():
                if dns_record.name in ACTUAL_SUBDOMAINS+ACTUAL_UNPROXIED_SUBDOMAINS and dns_record.ip != current_ip:
                    logging.info(f"Updating {dns_record.name}'s IP from {dns_record.ip} to {current_ip}")
                    dns_record.ip = current_ip
                    cloudflare.update_record(dns_record)
                    logging.info(f"\t{dns_record.name} has been updated.")
        except Exception as e:
            logging.error(f"Encountered exception:\n{e}\n\n will attempt again next loop.")
        sleep(int(DDNS_UPDATE_FREQ))

if __name__ == "__main__":
    set_dns()
    ddns_loop()
