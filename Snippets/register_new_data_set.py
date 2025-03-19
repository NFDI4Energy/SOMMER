import json
import os
import requests
import json
import sys
import hashlib
from urllib.parse import urlparse

API_KEY = "XXXXX"
MOSS_API_KEY = "YYYY"
ACCOUNT_NAME = "ZZZZ"
# OR jsut hard-code it if you do not want to change your env variables

DATABUS_URI_BASE = "https://databus.dev.dbpedia.link"
MOSS_URI_BASE = "https://moss.dev.dbpedia.link"

OTMETADATAFILE = "D:/NFDI4Energy/SOMMER/bnetza_charging_stations_normalised_01_12_2024/bnetza_charging_stations_normalised_01_12_2024.json"

with open(OTMETADATAFILE, mode ="r") as json_datei:
    DATEN = json.load(json_datei)

print("read json")
TITLE = DATEN.get('title')
DESCRIPTION = DATEN.get('description')
DATABUSID = DATEN.get('@id')
PARTS_OF_DATABUSID = DATABUSID.split('/')
USERNAME = PARTS_OF_DATABUSID[3]
GROUP_SLUG = PARTS_OF_DATABUSID[4]
ARTIFACT = PARTS_OF_DATABUSID[5]
VERSION = PARTS_OF_DATABUSID[6]
Number_of_licenses = 0
#LICENSE_LIST = DATEN.get('license',{}).get('licenses')
#for SINGE_LICENSE in LICENSE_LIST:
#    LICENSE[Number_of_licenses] = SINGE_LICENSE.get('link')
#    Number_of_licenses += 1
LICENSE = DATEN['licenses'][0]['path']
ID = DATEN['@id']
##########################
# Create artifact
##########################
headers = {
    "accept": "application/json",
    "Content-Type": "application/ld+json",
    "x-api-key": f"{API_KEY}",
}

payload = {
    "@context" : "https://databus.openenergyplatform.org/res/context.jsonld",
    "@graph": {
        "@id": f"{DATABUS_URI_BASE}/{ACCOUNT_NAME}/{GROUP_SLUG}/{ARTIFACT}",
        "@type": "Artifact",
        "title": f"{TITLE}",
        "description": f"{DESCRIPTION}",
    },
}
r = requests.post(
    f"{DATABUS_URI_BASE}/api/publish",
    data=json.dumps(payload),
    headers=headers,
)
print (r.content)
##########################
# Create version
##########################
payload = {
    "@context" : "https://databus.openenergyplatform.org/res/context.jsonld",
    "@graph": {
        "@type": [
          "Version",
          "Dataset"
        ],
        "@id": f"{DATABUS_URI_BASE}/{ACCOUNT_NAME}/{GROUP_SLUG}/{ARTIFACT}/{VERSION}",
        "hasVersion": f"{VERSION}",
        "title": f"{TITLE}",
        "abstract": f"{DESCRIPTION}",
        "description": f"{DESCRIPTION}",
        "license": f"{LICENSE}",
        "attribution": "Developed by DLR",
        "distribution": [
        ] 
    },
}
Number_of_resources = 0;
RESOURCE_LIST = DATEN.get('resources')
for RESOURCE in RESOURCE_LIST:
    file_size = 0;
    parsed_url = urlparse(DATEN['resources'][Number_of_resources]['path'])
    file_name = parsed_url.path.split('/')[-1]
    response = requests.get(DATEN['resources'][Number_of_resources]['path'], stream=True)
    if response.status_code == 200:
        sha256_hash = hashlib.sha256()
        for chunk in response.iter_content(1024):
            sha256_hash.update(chunk)
            file_size += len(chunk)
        checksum = sha256_hash.hexdigest()
    else:
        checksum = 123456789
    distribution_item = {
        "@type": "Part",
        "@id": f"{DATABUS_URI_BASE}/{ACCOUNT_NAME}/{GROUP_SLUG}/{ARTIFACT}/{VERSION}#{file_name}",
        "dcv:file": f"{file_name}",
        "formatExtension": f"{DATEN['resources'][Number_of_resources]['format']}",
        "compression": "none",
        "downloadURL": f"{DATEN['resources'][Number_of_resources]['path']}",
        "byteSize": f"{file_size}",
        "sha256sum": f"{checksum}"
    }
    Number_of_resources += 1; 
    payload["@graph"]["distribution"].append(distribution_item)
r = requests.post(
    f"{DATABUS_URI_BASE}/api/publish",
    data=json.dumps(payload),
    headers=headers,
)
print (r.content)
##########################
# Push Metadata to MOSS
##########################
headers = {
    "accept": "application/json",
    "Content-Type": "application/ld+json",
    "x-api-key": f"{MOSS_API_KEY}",
}
r = requests.post(
    f"{MOSS_URI_BASE}/api/save?layer=layer:openenergy&resource={ID}",
    data=json.dumps(DATEN, indent=4),
    headers=headers,
)
print (r.content)