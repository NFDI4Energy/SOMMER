import json
#import os
import requests
import certifi
#import sys
import hashlib
from urllib.parse import urlparse

ACCOUNT_NAME = "choyerklick"
GROUP = "OEPlatform"
#############
# SETUP for databus.dev.dbpedia.link
API_KEY = "XXXXX"
MOSS_API_KEY = "YYYY"
DATABUS_URI_BASE = "https://databus.dev.dbpedia.link"
MOSS_URI_BASE = "https://moss.dev.dbpedia.link"
##############

# The fuction ersetze_id_felder fixes empty @id entries which mess up validation at MOSS, needs a better fix in the data or validation, 
# this is quick work around for the demos at Forschungsnetzwerk Systemanalyse and HMC conference 2025. 
def ersetze_id_felder(daten, neuer_wert):
    if isinstance(daten, dict):  # Wenn es ein Dictionary ist
        for schluessel, wert in daten.items():
            if schluessel == "@id" and wert is None:
                daten[schluessel] = neuer_wert
            else:
                ersetze_id_felder(wert, neuer_wert)
    elif isinstance(daten, list):  # Wenn es eine Liste ist
        for eintrag in daten:
            ersetze_id_felder(eintrag, neuer_wert)

def register2databusandmoss(URI):
    response = requests.get(URI)
    if response.status_code == 200:
        DATEN = json.loads(response.text)
    else:
        exit()
    print("read json")
    TITLE = DATEN.get('title')
    #DATABUSID = DATEN.get('@id')"
    #DATABUSID = f"https://databus.dev.dbpedia.link/{ACCOUNT_NAME}/{GROUP}/{DATEN.get('name')}/20250505"
    PARTS_OF_DATABUSID = URI.split('/')
    USERNAME = PARTS_OF_DATABUSID[3]
    GROUP_SLUG = PARTS_OF_DATABUSID[4]
    ARTIFACT = PARTS_OF_DATABUSID[5]
    VERSION = PARTS_OF_DATABUSID[6]
    RESOURCES_LIST = DATEN.get('resources')
    #RESOURCE_NUMBER = 0; 
    # if the dataset in OEMeta 2.0 does not contain a title, take the tiele from the first resource. This is an artifact of the migration 
    # from OEMeta 1.X to OEMeta 2.0. 
    for RESOURCE in RESOURCES_LIST:
        if not DATEN.get('title'):
            TITLE = RESOURCE.get('title')
            DESCRIPTION = RESOURCE.get('description')
            break
    if len(TITLE) > 99:
        with open('D:/NFDI4Energy/SOMMER/local_tools/OEdatabus_entries_with_errors.txt','a') as error_file:
            error_file.write('Title longer than 100 characters: '+URI+'\n')
        print ('Title longer than 100 charcters' + URI)
        LONGTITLE = TITLE
        TITLE = LONGTITLE[:99]
    DESCRIPTION = DATEN.get('description')
    ABSTRACT = DESCRIPTION[:299]
    if len(DESCRIPTION) > 299:
        with open('D:/NFDI4Energy/SOMMER/local_tools/OEdatabus_entries_with_errors.txt','a') as error_file:
            error_file.write('Abstract shortend to 300 characters: '+URI+'\n')
        print ('Abstract shortend to 300 charcters' + URI)
    LICENSE = ""
    for RESOURCE in RESOURCES_LIST:
        LICENSE_LIST = RESOURCE.get('licenses')
        for SINGE_LICENSE in LICENSE_LIST:
            LICENSE = SINGE_LICENSE.get('path')
            break
        if LICENSE:
            break
    ##########################
    # Create artifact
    ##########################
    headers = {
        "accept": "application/json",
        "Content-Type": "application/ld+json",
        "x-api-key": f"{API_KEY}",
    }
    payload_abstract = {
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
        "@context" : f"{DATABUS_URI_BASE}/res/context.jsonld",
    #    "@context": "https://databus.dev.dbpedia.link/res/context.jsonld",
        "@graph": {
            "@type": "Version",
            "@id": f"{DATABUS_URI_BASE}/{ACCOUNT_NAME}/{GROUP_SLUG}/{ARTIFACT}/{VERSION}",
            "hasVersion": f"{VERSION}",
            "title": f"{TITLE}",
            "abstract": f"{ABSTRACT}",
            "description": f"{DESCRIPTION}",
            "license": f"{LICENSE}",
            "attribution": "Developed by DLR",
            "distribution": [
            ] 
        },    
    }
    for RESOURCE in RESOURCES_LIST:
        file_size = 0
        number_of_files = 0
        errormsg = 'path does not contain a valid URL'
        path = RESOURCE.get('path')
        parsed_url = urlparse(path)
        if parsed_url.scheme and parsed_url.netloc:
            file_name = parsed_url.path.split('/')[-1]
            response = requests.get(path, stream=True)
            if response.status_code == 200:
                sha256_hash = hashlib.sha256()
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
            data=json.dumps(payload_abstract),
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
    else:
        with open('D:/NFDI4Energy/SOMMER/local_tools/OEdatabus_entries_with_errors.txt','a') as error_file:
            error_file.write(errormsg + ': '+URI+'\n')
        print (errormsg + ' ' + path)
    ##########################
    # Add @context
    ##########################
    context = "https://moss.dev.dbpedia.link/context/openenergy.jsonld"
    DATEN['@context'] = context
    DATEN['@id'] = f"{DATABUS_URI_BASE}/{ACCOUNT_NAME}/{GROUP_SLUG}/{ARTIFACT}/{VERSION}"
    ersetze_id_felder(DATEN,"None")
    ##########################
    # Push Metadata to MOSS
    ##########################
    headers = {
        "accept": "application/json",
        "Content-Type": "application/ld+json",
        "x-api-key": f"{MOSS_API_KEY}",
    }
    if number_of_files > 0:
        r = requests.post(
            f"{MOSS_URI_BASE}/api/save?layer=layer:openenergy&resource={DATABUS_URI_BASE}/{ACCOUNT_NAME}/{GROUP_SLUG}/{ARTIFACT}/{VERSION}",
            data=json.dumps(DATEN, indent=4),
            headers=headers,
        )
        if r.status_code == 200:
            print ('MOSS submitted')
        else:
            print ('MOSS error')
            print (r.content)
            with open('D:/NFDI4Energy/SOMMER/local_tools/OEdatabus_entries_with_errors.txt','a') as error_file:
                error_file.write('MOSS error :'+URI+'\n')
                response_json = r.json()
                error_file.write(f"{response_json.get('message')}\n")
                print ('MOSS error ' + path)
    # end of def register2databusandmoss(URI):
##################################
# Main program
##################################
with open('D:/NFDI4Energy/SOMMER/local_tools/OEdatabus_entries_with_errors.txt','w') as error_file:
    error_file.write('OEDatabus Entries with errors\n')
with open('D:/NFDI4Energy/SOMMER/Snippets/OEdatabus_list.txt','r') as file:
    for line in file:
        if "oeplatform" in line:
            databus_id = line.strip()
            databus_part = databus_id.split('/')
            user = databus_part[3]
            group = databus_part[4]
            artifact = databus_part[5]
            version = databus_part[6]
            databus_url =f"{databus_id}/{artifact}_variant=metadata.json"
            databus_response = requests.get(databus_url)
            if databus_response.status_code == 200:
                print(f"registering {databus_url}")
                register2databusandmoss(databus_url)
            else:
                print(f"{databus_url} not found!")
