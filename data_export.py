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

SPIDER_RESULTS_ENTITY_KIND = 'spider-results-dev'

client = None

def export_results():
    """
    Export of the main results data
    """
    out = []

    # Load data from database
    query = client.query(kind=SPIDER_RESULTS_ENTITY_KIND)
    for entity in query.fetch():
        logging.debug(entity.key.name)
        out.append({
            'input_url': entity.key.name,
            'resulting_urls': entity.get('checks').get('url_canonicalization'),
            'created': entity.get('created').isoformat(),
            'meta': entity.get('meta'),
            'checks': entity.get('checks'),
            'rating': entity.get('rating'),
            'score': entity.get('score'),
            'icons': [],
        })
    
    # load icons, reformat icons details
    for index in range(len(out)):
        assert "checks" in out[index]
        assert "html_head" in out[index]["checks"]
        
        # collect icons urls
        icons = set()
        for url in out[index]['checks']['html_head']:
            assert 'link_icon' in out[index]['checks']['html_head'][url]
            if out[index]['checks']['html_head'][url]['link_icon'] is not None:
                icons.add(out[index]['checks']['html_head'][url]['link_icon'])
        
        out[index]["icons"] = {}
        for iconurl in list(icons):
            logging.debug("Dowloading icon %s", iconurl)
            filename = download_icon(iconurl)
            if filename:
                out[index]["icons"][url] = filename

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
        if 'screenshot_url' not in item:
            logging.error("Export failed. No 'screenshot_url' attribute set in dataset. %s\n" % item)
            return
        logging.debug("url: %s, screenshot_url: %s" % (item['url'], item['screenshot_url']))
        filename = os.path.basename(item['screenshot_url'])
        out[item['url']] = filename
    
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

    # TODO: Re-enable
    #export_screenshots()
    export_results()
