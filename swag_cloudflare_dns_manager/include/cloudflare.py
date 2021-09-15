import logging
import requests
import os

CF_API_EMAIL = os.getenv("CF_API_EMAIL", default = None)
CF_API_KEY = os.getenv("CF_API_KEY", default = None)
CF_ZONE_ID = os.getenv("CF_ZONE_ID", default = None)
missing_env_vars = [v for v in (CF_API_EMAIL, CF_API_KEY, CF_ZONE_ID) if v is None]
if missing_env_vars:
    raise Exception(f"Missing env vars: {missing_env_vars}")

HEADERS = {
    "X-Auth-Email": CF_API_EMAIL,
    "X-Auth-Key": CF_API_KEY,
    "Content-Type": "application/json"
}

def get_current_ip():
    ip = requests.get('https://api.ipify.org').text
    return ip

CURRENT_IP = get_current_ip()

class DNSRecord:
  def __init__(self, dns_name, dns_ip=None, dns_id=None):
      self.name = dns_name
      self.id = dns_id
      self.ip = dns_ip

def get_records(print_log=True):
    logging.info("Getting Existing DNS Records Of Type A")
    r=requests.get(f"https://api.cloudflare.com/client/v4/zones/{CF_ZONE_ID}/dns_records?type=A&per_page=100", headers=HEADERS)
    result = r.json()['result']
    logging.info(f"\tGathered {len(result)} existing DNS records")
    return [DNSRecord(dns_name=dns['name'], dns_ip=dns['content'], dns_id=dns['id']) for dns in result]

def create_record(dns_record):
    record_data = {
        "type": "A",
        "name": dns_record.name,
        "content": dns_record.ip,
        "ttl": 1,
        "proxied": True
    }
    r=requests.post(f"https://api.cloudflare.com/client/v4/zones/{CF_ZONE_ID}/dns_records", json=record_data, headers=HEADERS)
    logging.debug(r.text)
    return


def update_record(dns_record):
    record_data = {
        "type": "A",
        "name": dns_record.name,
        "content": dns_record.ip,
        "ttl": 1,
        "proxied": True
    }
    r=requests.put(f"https://api.cloudflare.com/client/v4/zones/{CF_ZONE_ID}/dns_records/{dns_record.id}", json=record_data, headers=HEADERS)
    logging.debug(r.text)
    return


# def delete_record(dns_record):
#     logging.info(f"Deleting DNS Record {dns_record.name}")
#     r=requests.delete(f"https://api.cloudflare.com/client/v4/zones/{CF_ZONE_ID}/dns_records/{dns_record.id}", headers=HEADERS)

#     logging.info(f"\t{dns_record.name} has been deleted.")
#     return
