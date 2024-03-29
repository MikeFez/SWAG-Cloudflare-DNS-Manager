from include import cloudflare
import logging
from time import sleep
import os

logging.basicConfig(level=logging.INFO)

def get_or_revert_to_none(env_var, as_int=False):
    var = os.getenv(env_var, default=None)
    if var is None or var == "":
        return None
    else:
        if as_int:
            var = int(var)
    return var

class ENV_VARS:
    DOMAIN = os.getenv("DOMAIN", default = None)
    PROXIED_RECORDS_RAW = os.getenv("PROXIED_RECORDS", default = None)
    UNPROXIED_RECORDS_RAW = os.getenv("UNPROXIED_RECORDS", default = None)
    DDNS_UPDATE_FREQ = get_or_revert_to_none("DDNS_UPDATE_FREQ", as_int=True)
    DELETE_ACME_RECORDS = os.getenv("DELETE_ACME_RECORDS", default = None).lower() == "true"
    DELETE_ACME_RECORDS_WAIT = get_or_revert_to_none("DELETE_ACME_RECORDS_WAIT", as_int=True)

missing_env_vars = [k for k, v in vars(ENV_VARS).items() if not k.startswith("_") and v is None]
if missing_env_vars:
    raise Exception(f"Missing env vars: {missing_env_vars}")

PROXIED_RECORDS = [f"{rec}.{ENV_VARS.DOMAIN}" for rec in ENV_VARS.PROXIED_RECORDS_RAW.split(",") if rec not in (ENV_VARS.DOMAIN, '')]
UNPROXIED_RECORDS = [f"{rec}.{ENV_VARS.DOMAIN}" for rec in ENV_VARS.UNPROXIED_RECORDS_RAW.split(",") if rec not in (ENV_VARS.DOMAIN, '')] if ENV_VARS.UNPROXIED_RECORDS_RAW is not None else []
for rec in UNPROXIED_RECORDS:
    if rec in PROXIED_RECORDS:
        PROXIED_RECORDS.remove(rec)

RECORD_NAMES_BY_PROXY_TYPE = {
        True: PROXIED_RECORDS,
        False: UNPROXIED_RECORDS
    }

logging.info("Proxied Items To Monitor:\n\t" + "\n\t".join(RECORD_NAMES_BY_PROXY_TYPE[True]))
logging.info("Unproxied Items To Monitor:\n\t" + "\n\t".join(RECORD_NAMES_BY_PROXY_TYPE[False]))

def set_dns():
    current_ip = cloudflare.get_current_ip()
    existing_records_names = [rec.name for rec in cloudflare.get_records()]

    # Discover new
    records_added = 0
    for proxy_enabled, record_names in RECORD_NAMES_BY_PROXY_TYPE.items():
        for record in record_names:
            if record not in existing_records_names:
                logging.info(f"Creating DNS Record for {record}")
                cloudflare.create_record(cloudflare.DNSRecord(dns_name=record,
                                                            dns_ip=current_ip,
                                                            dns_proxied=proxy_enabled))
                logging.info(f"\t{record} has been created.")
                records_added += 1
    if records_added > 0:
        logging.info(f"Added {records_added} new DNS record{'s' if records_added > 0 else ''}")
    else:
        logging.info("No DNS records needed to be added")

def delete_acme_records():
    logging.info("Starting acme record cleanup")
    challenge_prefix = "_acme-challenge."
    try:
        txt_records = cloudflare.get_records(type="TXT")
        if txt_records > 0:
            logging.info(f"\t{len(txt_records)} acme challenge{'s' if txt_records > 0 else ''} exist")
        else:
            logging.info("\tNo acme challenges needed to be deleted")

        for record in txt_records:
            if any(f"{challenge_prefix}.{x}" in record.name for x in PROXIED_RECORDS+UNPROXIED_RECORDS):
                cloudflare.delete_record(record)
            else:
                logging.info(f"\tSkipping {record.name}")

    except Exception as e:
        logging.error(f"Encountered exception:\n{e}")


def ddns_loop():
    while True:
        try:
            #TODO: check if proxy type accurate
            logging.info("Checking For DDNS Updates")
            current_ip = cloudflare.get_current_ip()
            existing_records_by_name = {rec.name: rec for rec in cloudflare.get_records()}
            for proxy_type, rec_names in RECORD_NAMES_BY_PROXY_TYPE.items():
                for rec_name in rec_names:
                    if rec_name in existing_records_by_name:
                        dns_record = existing_records_by_name[rec_name]
                        update_should_occur = False
                        if dns_record.ip != current_ip:
                            logging.info(f"\t{rec_name}'s IP must be updated from {dns_record.ip} to {current_ip}")
                            update_should_occur = True
                        if dns_record.proxied != proxy_type:
                            logging.info(f"\t{rec_name}'s proxy status must be updated from {dns_record.proxied} to {proxy_type}")
                            update_should_occur = True
                        if update_should_occur:
                            dns_record.ip = current_ip
                            dns_record.proxied = proxy_type
                            cloudflare.update_record(dns_record)
                            logging.info(f"\t\t{rec_name} has been updated.")
                        else:
                            logging.info(f"\t{rec_name} does not need to be updated.")
        except Exception as e:
            logging.error(f"Encountered exception:\n{e}\n\n Will attempt again next loop.")
        logging.info(f"Waiting {ENV_VARS.DDNS_UPDATE_FREQ} seconds till next check.")
        sleep(ENV_VARS.DDNS_UPDATE_FREQ)

if __name__ == "__main__":
    set_dns()
    if ENV_VARS.DELETE_ACME_RECORDS:
        sleep(ENV_VARS.DELETE_ACME_RECORDS_WAIT) # Wait X seconds for acme challenges to have been completed
        delete_acme_records() # Delete acme challenge records
    ddns_loop() # Start the DDNS IP update loop
