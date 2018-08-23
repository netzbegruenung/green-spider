"""
Exports data from the database to JSON files for use in a static webapp
"""

from google.cloud import datastore
import json
import sys
import os


client = None

def export_results():
    """
    Export of the main results data
    """
    out = []

    query = client.query(kind='spider-results')
    for entity in query.fetch():
        print(entity.key.name)
        out.append(dict(entity)["results"])
    
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
        print(item['url'], os.path.basename(item['screenshot_url']))
        out[item['url']] = os.path.basename(item['screenshot_url'])
    
    output_filename = "/out/screenshots.json"
    with open(output_filename, 'w', encoding="utf8") as jsonfile:
        json.dump(out, jsonfile, indent=2, sort_keys=True, ensure_ascii=False)


if __name__ == "__main__":
    if len(sys.argv) == 1:
        print("Error: please provide path to Google Storage API system account JSON file as argument")
        sys.exit(1)

    key_path = sys.argv[1]
    client = datastore.Client.from_service_account_json(key_path)
    
    export_screenshots()
    export_results()
