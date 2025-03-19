import json
import os
import requests

API_KEY = "XXXX"
ACCOUNT_NAME = "ACCOUNT-NAME"
# OR jsut hard-code it if you do not want to change your env variables

DATABUS_URI_BASE = "https://databus.dev.dbpedia.link"
TITLE = "SOMMER (Search over Multi-Domain Metadata for NFDI Respositories)"
DESCRIPTION = "Group for the Demonstration of databus and MOSS within the Workshops of the SOMMER (Search over Multi-Domain Metadata for NFDI Repositories) project."
GROUP_SLUG = "SOMMER"
# CREATE GROUP
headers = {
    "accept": "application/json",
    "Content-Type": "application/ld+json",
    "x-api-key": f"{API_KEY}",
}

payload = {
    "@context": "https://downloads.dbpedia.org/databus/context.jsonld",
    "@graph": {
        "@id": f"{DATABUS_URI_BASE}/{ACCOUNT_NAME}/{GROUP_SLUG}",
        "@type": "Group",
        "title": f"{TITLE}",
        "description": f"{DESCRIPTION}",
    },
}

r = requests.put(
    f"{DATABUS_URI_BASE}/{ACCOUNT_NAME}/{GROUP_SLUG}",
    data=json.dumps(payload),
    headers=headers,
)
print (r.content)

