import json
import requests
import hashlib
from urllib.parse import urlparse

API_KEY = "XXXX"
ACCOUNT_NAME = "YYYY"
# OR just hard-code it if you do not want to change your env variables

DATABUS_URI_BASE = "https://databus.dev.dbpedia.link"

OTMETADATAFILE = "D:/NFDI4Energy/SOMMER/local_tools/sedos_tra_demand.json"

with open(OTMETADATAFILE, mode ="r") as json_datei:
    DATEN = json.load(json_datei)

print("read json")
RESOURCES_LIST = DATEN.get('resources')
# if the dataset in OEMeta 2.0 does not contain a title, take the tiele from the first resource. This is an artifact of the migration 
# from OEMeta 1.X to OEMeta 2.0. 
for RESOURCE in RESOURCES_LIST:
    if not DATEN.get('title'):
        TITLE = RESOURCE.get('title')
        DESCRIPTION = RESOURCE.get('description')
        break
if len(TITLE) > 99:
    LONGTITLE = TITLE
    TITLE = LONGTITLE[:99]
DESCRIPTION = DATEN.get('description')
ABSTRACT = DESCRIPTION[:299]
if len(DESCRIPTION) > 299:
        print ('Abstract shortend to 300 charcters')
LICENSE = ""
for RESOURCE in RESOURCES_LIST:
    LICENSE_LIST = RESOURCE.get('licenses')
    for SINGE_LICENSE in LICENSE_LIST:
        LICENSE = SINGE_LICENSE.get('path')
        break
    if LICENSE:
        break
DATABUSID = DATEN.get('@id')
PARTS_OF_DATABUSID = DATABUSID.split('/')
USERNAME = PARTS_OF_DATABUSID[3]
GROUP_SLUG = PARTS_OF_DATABUSID[4]
ARTIFACT = PARTS_OF_DATABUSID[5]
VERSION = PARTS_OF_DATABUSID[6]
ID = DATEN['@id']
##########################
# Create artifact
##########################
headers = {
    "accept": "application/json",
    "Content-Type": "application/ld+json",
    "x-api-key": f"{API_KEY}",
}
payload_artifact = {
    "@context" : f"{DATABUS_URI_BASE}/res/context.jsonld",
    "@graph": {
        "@id": f"{DATABUS_URI_BASE}/{ACCOUNT_NAME}/{GROUP_SLUG}/{ARTIFACT}",
        "@type": "Artifact",
        "title": f"{TITLE}",
        "description": f"{DESCRIPTION}",
    },
}
##########################
# Create version
##########################
payload_version = {
    "@graph": {
        "@context" : f"{DATABUS_URI_BASE}/res/context.jsonld",
        "@type":"Version",
        "@id": f"{DATABUS_URI_BASE}/{ACCOUNT_NAME}/{GROUP_SLUG}/{ARTIFACT}/{VERSION}",
        "hasVersion": f"{VERSION}",
        "title": f"{TITLE}",
        "abstract": f"{DESCRIPTION}",
        "description": f"{DESCRIPTION}",
        "license": f"{LICENSE}",
        "attribution": "Developed by ABCD",
        "distribution": [
        ] 
    }   
}
RESOURCE_LIST = DATEN.get('resources')
for RESOURCE in RESOURCE_LIST:
    number_of_files = 0
    path = RESOURCE.get('path')
    parsed_url = urlparse(path)
    if parsed_url.scheme and parsed_url.netloc:
        file_name = parsed_url.path.split('/')[-1]
        response = requests.get(path, stream=True)
        if response.status_code == 200:
            sha256_hash = hashlib.sha256()
            file_size = 0
            for chunk in response.iter_content(1024):
                sha256_hash.update(chunk)
                file_size += len(chunk)
        checksum = sha256_hash.hexdigest()
        number_of_files += 1
        distribution_item = {
            "@type": "Part",
            "@id": f"{DATABUS_URI_BASE}/{ACCOUNT_NAME}/{GROUP_SLUG}/{ARTIFACT}/{VERSION}#{file_name}",
            "dcv:file": f"{RESOURCE.get('name')}",
            "formatExtension": f"{RESOURCE.get('format')}",
            "compression": "none",
            "downloadURL": f"{path}",
            "byteSize": f"{file_size}",
            "sha256sum": f"{checksum}"
        }
        payload_version["@graph"]["distribution"].append(distribution_item)
    else:
        errormsg = 'path is not accessible'   
if number_of_files > 0:
    r = requests.post(
        f"{DATABUS_URI_BASE}/api/publish",
        data=json.dumps(payload_artifact),
        headers=headers,
        )
    if r.status_code == 200:
        print ('Artifact submitted')
        print (r.content)
    else:
        print ('Artifact error')
        print (r.content)
        exit(1)
    r = requests.post(
        f"{DATABUS_URI_BASE}/api/publish", 
        data=json.dumps(payload_version),
        headers=headers,
        )
    if r.status_code == 200:
        print ('Version submitted')
        print (r.content)
    else:
        print ('Version error')
        print (r.content)
        exit(1) 
