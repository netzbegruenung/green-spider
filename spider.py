# coding: utf8

from git import Repo
from multiprocessing import Pool
from urllib.parse import urlparse
from socket import gethostbyname_ex
import json
import logging
import os
import random
import requests
import shutil
import sys
import yaml
import json

# configuration

# number of parallel processes to use for crawling
concurrency = 6

# connection timeout for website checks (seconds)
connect_timeout = 5

# response timeout for website checks
read_timeout = 10

# Git repo for our data
green_directory_repo = 'https://github.com/netzbegruenung/green-directory.git'
# folder in that repo that holds the data
green_direcory_data_path = 'data'
green_directory_local_path = './cache/green-directory'


# end configuration

def get_green_directory():
    """
    Clones the green directory into the local file system
    """
    if os.path.exists(green_directory_local_path):
        shutil.rmtree(green_directory_local_path)
    Repo.clone_from(green_directory_repo, green_directory_local_path)


def dir_entries():
    path = os.path.join(green_directory_local_path, green_direcory_data_path)
    for root, dirs, files in os.walk(path):
        for fname in files:

            filepath = os.path.join(root, fname)
            if not filepath.endswith(".yaml"):
                continue

            with open(filepath, 'r') as yamlfile:
                for doc in yaml.load_all(yamlfile):
                    yield doc

def repr_entry(entry):
    """
    Return string representation of an entry
    """
    r = entry['type']
    if 'level' in entry:
        r += "/" + entry['level']
    if 'state' in entry:
        r += "/" + entry['state']
    if 'district' in entry:
        r += "/" + entry['district']
    return r

def resolve_hostname(url):
    parsed = urlparse(url)
    hostname, aliaslist, ipaddrlist = gethostbyname_ex(parsed.hostname)
    return (parsed.scheme, hostname, aliaslist, ipaddrlist)

def check_site(url):
    """
    Performs our site check and returns results as a dict
    """
    result = {
        'status_code': 0,
        'error': None,
        'redirects': 0,
        'final_url': None,
        'hostname': None,
        'scheme': None,
        'aliases': None,
        'ip_addresses': None,
        'duration': 0,
    }

    try:
        (scheme, hostname, aliases, ip_addresses) = resolve_hostname(url)
        result['scheme'] = scheme
        result['hostname'] = hostname
        result['aliases'] = aliases
        result['ip_addresses'] = ip_addresses
    except Exception as e:
        logging.error(str(e) + " " + url)

    headers = {
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 green-spider/0.1'
    }

    try:
        r = requests.get(url, headers=headers, timeout=(connect_timeout, read_timeout))
        result['status_code'] = r.status_code
        if len(r.history) > 0:
            result['redirects'] = len(r.history)
            result['final_url'] = r.url
        result['duration'] = round(r.elapsed.microseconds / 1000)
    except requests.exceptions.ConnectionError as e:
        logging.error(str(e) + " " + url)
        result['error'] = "connection"
    except requests.exceptions.Timeout as e:
        logging.error(str(e) + " " + url)
        result['error'] = "connection_timeout"
    except requests.exceptions.ReadTimeout as e:
        logging.error(str(e) + " " + url)
        result['error'] = "read_timeout"
    except Exception as e:
        logging.error(str(e) + " " + url)
        result['error'] = "unknown"

    logging.info("%s done" % url)
    return result

def main():
    logging.basicConfig(level=logging.INFO)

    get_green_directory()

    urls = []
    for entry in dir_entries():

        if 'type' not in entry:
            logging.error("Entry without type")
            continue

        if 'urls' not in entry:
            logging.info("Entry %s does not have any URLs." % repr_entry(entry))
            continue

        website_url = None
        for n in range(len(entry['urls'])):
            try:
                if entry['urls'][n]['type'] == "WEBSITE":
                    website_url = entry['urls'][n]['url']
            except NameError as ne:
                logging.error("Error in %s: 'url' key missing (%s)" % (repr_entry(entry), entry['urls'][n]))
        if website_url:
            urls.append(website_url)

    random.seed()
    random.shuffle(urls)

    results = {}

    if concurrency > 1:
        pool = Pool(concurrency)
        for url in urls:
            results[url] = pool.apply_async(check_site, kwds={"url": url})
        pool.close()
        pool.join()
    else:
        for url in urls:
            results[url] = check_site(url)

    results2 = {}

    for url in results.keys():
        results2[url] = results[url].get()

    with open('result.json', 'w', encoding="utf8") as jsonfile:
        json.dump(results2, jsonfile, indent=2, sort_keys=True)


if __name__ == "__main__":
    main()
