# coding: utf8

from bs4 import BeautifulSoup
from git import Repo
from multiprocessing import Pool
from socket import gethostbyname_ex
from urllib.parse import urlparse
import certifi
import json
import logging
import os
import random
import re
import requests
import shutil
import sys
import yaml

# configuration

# number of parallel processes to use for crawling
concurrency = 4

# connection timeout for website checks (seconds)
connect_timeout = 5

# response timeout for website checks
read_timeout = 10

# Git repo for our data
green_directory_repo = 'https://github.com/netzbegruenung/green-directory.git'
# folder in that repo that holds the data
green_direcory_data_path = 'data'
green_directory_local_path = './cache/green-directory'

result_path = './webapp/dist/data'

# end configuration


def get_green_directory():
    """
    Clones the source of website URLs, the green directory,
    into the local file system using git
    """
    if os.path.exists(green_directory_local_path):
        shutil.rmtree(green_directory_local_path)
    Repo.clone_from(green_directory_repo, green_directory_local_path)


def dir_entries():
    """
    Iterator over all data files in the cloned green directory
    """
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
    Return string representation of a directory entry,
    for logging/debugging purposes
    """
    r = entry['type']
    if 'level' in entry:
        r += "/" + entry['level']
    if 'state' in entry:
        r += "/" + entry['state']
    if 'district' in entry:
        r += "/" + entry['district']
    return r


def derive_test_hostnames(hostname):
    """
    Derives the hostnames variants to test for a given host name.
    From 'gruene-x.de' or 'www.gruene-x.de' it makes

      ['gruene-x.de', 'www.gruene-x.de']

    which are both plausible web URLs to be used for a domain.
    """

    hostnames = set()

    hostnames.add(hostname)
    if hostname.startswith('www.'):
        hostnames.add(hostname[4:])
    else:
        hostnames.add('www.' + hostname)

    return list(hostnames)


def reduce_urls(urllist):
    """
    Reduce a list of urls with metadata by eliminating those
    that either don't work or lead somewhere else
    """
    targets = set()
    for u in urllist:
        if u['error'] is not None:
            continue
        if u['redirects_to'] is not None:
            targets.add(u['redirects_to'])
        else:
            targets.add(u['url'])
    return list(targets)


def normalize_title(s):
    """
    Removes garbage from HTML page titles
    """
    s = s.replace('\u00a0', ' ')
    s = s.replace('  ', ' ')
    s = s.strip()
    return s

def check_content(r):
    """
    Adds details to check regarding content of the page

    check: the dict containing details for this URL
    r: requests request/response object
    """
    result = {}

    result['encoding'] = r.encoding
    soup = BeautifulSoup(r.text, 'html.parser')

    # page title
    result['title'] = None
    title = soup.find('head').find('title')
    if title is not None:
        result['title'] = normalize_title(title.get_text())

    # canonical link
    result['canonical_link'] = None
    link = soup.find('link', rel='canonical')
    if link:
        result['canonical_link'] = link.get('href')

    # feed links
    result['feeds'] = []
    rss_links = soup.find_all('link', type='application/rss+xml')
    atom_links = soup.find_all('link', type='application/atom+xml')

    if len(rss_links) > 0:
        for l in rss_links:
            result['feeds'].append(l.get('href'))
    if len(atom_links) > 0:
        for l in rss_links:
            result['feeds'].append(l.get('href'))

    # generator meta tag
    result['generator'] = None
    generator = soup.head.select('[name=generator]')
    if len(generator):
        result['generator'] = generator[0].get('content')

    # opengraph meta tags
    result['opengraph'] = None
    og = set()
    for item in soup.head.find_all(property=re.compile('^og:')):
        og.add(item.get('property'))
    for item in soup.head.find_all(itemprop=re.compile('^og:')):
        og.add(item.get('itemprop'))
    if len(og):
        result['opengraph'] = list(og)

    return result

def check_site(url):
    """
    Performs our site check and returns results as a dict.

    1. Normalize the input URL and derive the URLs to check for
    2. HEAD the check urls
    3. Determine the canonical URL
    4. Run full check on canonical URL
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 green-spider/0.1'
    }

    result = {
        'input_url': url,
        'hostnames': [],
        'resolvable_urls': [],
        'canonical_urls': [],
        'urlchecks': [],
    }

    # derive hostnames to test
    parsed = urlparse(url)
    hostnames = derive_test_hostnames(parsed.hostname)


    processed_hostnames = []
    for hn in hostnames:

        record  = {
            'input_hostname': hn,
            'resolvable': False,
        }

        try:
            hostname, aliases, ip_addresses = gethostbyname_ex(hn)
            record['resolvable'] = True
            record['resolved_hostname'] = hostname
            record['aliases'] = aliases
            record['ip_addresses'] = ip_addresses
        except:
            pass

        processed_hostnames.append(record)

    result['hostnames'] = sorted(processed_hostnames, key=lambda hn: hn['input_hostname'])

    checked_urls = []
    for item in processed_hostnames:
        if not item['resolvable']:
            continue

        for scheme in ('http', 'https'):

            record = {
                'url': scheme + '://' + item['resolved_hostname'] + '/',
                'error': None,
                'redirects_to': None,
            }

            try:
                r = requests.head(record['url'], headers=headers, allow_redirects=True)
                if r.url == url:
                    logging.info("URL: %s - status %s - no redirect" % (record['url'], r.status_code))
                else:
                    logging.info("URL: %s - status %s - redirects to %s" % (record['url'], r.status_code, r.url))
                    record['redirects_to'] = r.url
            except Exception as e:
                record['error'] = {
                    'type': str(type(e)),
                    'message': str(e),
                }
                logging.info("URL %s: %s %s" % (url, str(type(e)), e))

            checked_urls.append(record)

    result['resolvable_urls'] = sorted(checked_urls, key=lambda url: url['url'])
    result['canonical_urls'] = sorted(reduce_urls(checked_urls))

    # Deeper test for the remaining (canonical) URL(s)
    for check_url in result['canonical_urls']:

        logging.info("Checking URL %s" % check_url)

        check = {
            'url': check_url,
            'status_code': None,
            'duration': None,
            'error': None,
            'content': None,
        }

        try:
            r = requests.get(check_url, headers=headers, timeout=(connect_timeout, read_timeout))
            check['status_code'] = r.status_code
            check['duration'] = round(r.elapsed.microseconds / 1000)

            # Content checks
            if r.status_code < 300:
                check['content'] = check_content(r)

        except requests.exceptions.ConnectionError as e:
            logging.error(str(e) + " " + check_url)
            check['error'] = "connection"
        except requests.exceptions.Timeout as e:
            logging.error(str(e) + " " + check_url)
            check['error'] = "connection_timeout"
        except requests.exceptions.ReadTimeout as e:
            logging.error(str(e) + " " + check_url)
            check['error'] = "read_timeout"
        except Exception as e:
            logging.error(str(e) + " " + check_url)
            check['error'] = "unknown"

        result['urlchecks'].append(check)


    result['urlchecks'] = sorted(result['urlchecks'], key=lambda url: url['url'])

    return result


def main():
    logging.basicConfig(level=logging.INFO)
    logging.getLogger("urllib3").setLevel(logging.CRITICAL)

    get_green_directory()

    urls = []
    for entry in dir_entries():

        if 'type' not in entry:
            logging.error("Entry without type")
            continue

        if 'urls' not in entry:
            logging.debug("Entry %s does not have any URLs." % repr_entry(entry))
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

    results2 = []
    done = set()

    # convert results from ApplyResult to dict
    for url in sorted(results.keys()):
        if url not in done:
            results2.append(results[url].get())
        done.add(url)

    # Write result as JSON
    output_filename = os.path.join(result_path, "spider_result.json")
    with open(output_filename, 'w', encoding="utf8") as jsonfile:
        json.dump(results2, jsonfile, indent=2, sort_keys=True, ensure_ascii=False)


if __name__ == "__main__":
    main()
