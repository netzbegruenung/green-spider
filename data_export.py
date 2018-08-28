"""
Exports data from the database to JSON files for use in a static webapp
"""

from google.cloud import datastore
import hashlib
import json
import logging
import sys
import os

import requests


SITEICONS_PATH = "/icons"

client = None

def export_results():
    """
    Export of the main results data
    """
    out = []

    query = client.query(kind='spider-results')
    for entity in query.fetch():
        logging.debug(entity.key.name)
        out.append(dict(entity)["results"])
    
    # load icons, reformat icons details
    for index in range(len(out)):
        if "details" not in out[index]:
            continue
        if "icons" not in out[index]["details"]:
            continue
        urls = out[index]["details"]["icons"]
        out[index]["details"]["icons"] = {}
        for url in urls:
            if not (url.startswith("http://") or url.startswith("https://")):
                logging.debug("Skipping icon %s", url)
                continue
            logging.debug("Dowloading icon %s", url)
            filename = download_icon(url)
            if filename:
                out[index]["details"]["icons"][url] = filename

    output_filename = "/out/spider_result.json"
    with open(output_filename, 'w', encoding="utf8") as jsonfile:
        json.dump(out, jsonfile, indent=2, sort_keys=True, ensure_ascii=False)


def export_screenshots():
    """
    Export of screenshot meta data
    """
    out = {}

    query = client.query(kind='webscreenshot')
    for item in query.fetch():
        logging.debug(item['url'], os.path.basename(item['screenshot_url']))
        out[item['url']] = os.path.basename(item['screenshot_url'])
    
    output_filename = "/out/screenshots.json"
    with open(output_filename, 'w', encoding="utf8") as jsonfile:
        json.dump(out, jsonfile, indent=2, sort_keys=True, ensure_ascii=False)


def download_icon(icon_url):
    """
    Download an icon from the given URL and store it with
    a file name of <hash>.<ending>
    """

    default_endings = {
        "image/x-icon": "ico",
        "image/vnd.microsoft.icon": "ico",
        "image/png": "png",
        "image/jpeg": "jpg",
    }

    # Download the icon
    try:
        req = requests.get(icon_url, timeout=10)
    except:
        return None
    if req.status_code >= 400:
        return None

    content_hash = hashlib.md5(req.content).hexdigest()
    extension = ""

    try:
        file_name = os.path.basename(icon_url)[-1]
    except IndexError as exc:
        logging.error("Error in URL %s: %s", icon_url, exc)
        return None

    if file_name != "" and "." in file_name:
        ext = file_name.split(".")[-1]
        if ext != "":
            extension = ext

    if extension == "":
        # derive from content type
        ctype = req.headers.get('content-type')
        try:
            extension = default_endings[ctype]
        except KeyError:
            logging.error("No file ending defined for icon type '%s'", ctype)
            return None

    filename = content_hash + "." + extension.lower()

    path = SITEICONS_PATH + os.path.sep + filename
    with open(path, 'wb') as iconfile:
        iconfile.write(req.content)

    return filename


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    if len(sys.argv) == 1:
        print("Error: please provide path to Google Storage API system account JSON file as argument")
        sys.exit(1)

    key_path = sys.argv[1]
    client = datastore.Client.from_service_account_json(key_path)
    
    export_screenshots()
    export_results()
