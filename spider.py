# coding: utf8

from bs4 import BeautifulSoup
from git import Repo
from multiprocessing import Pool
from selenium import webdriver
from socket import gethostbyname_ex
from urllib.parse import urljoin
from urllib.parse import urlparse
import certifi
import json
import logging
import os
import random
import re
import requests
import shutil
import statistics
import sys
import yaml


# configuration

# number of parallel processes to use for crawling
concurrency = 3

# connection timeout for website checks (seconds)
connect_timeout = 5

# response timeout for website checks
read_timeout = 10

# Git repo for our data
green_directory_repo = 'https://github.com/netzbegruenung/green-directory.git'
# folder in that repo that holds the data
green_direcory_data_path = 'data/countries/de'
green_directory_local_path = './cache/green-directory'

result_path = './webapp/dist/data'

# IP address of the newthinking GCMS server
gcms_ip = "91.102.13.20"

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

def check_responsiveness(url):
    """
    Checks
    - whether a page adapts to different viewport sizes
    - whether a viewport meta tag exists
    and returns details
    """
    details = {
        'document_width': {},
        'viewport_meta_tag': None,
    }

    # sizes we check for (width, height)
    sizes = (
        (320,480), # old smartphone
        (768,1024), # older tablet or newer smartphone
        (1024,768), # older desktop or horiz. tablet
        (1920, 1080), # Full HD horizontal
    )

    # Our selenium user agent using PhantomJS/Webkit as an engine
    driver = webdriver.PhantomJS()
    driver.set_window_size(sizes[0][0], sizes[0][1])
    driver.get(url)

    for (width, height) in sizes:
        driver.set_window_size(width, height)
        key = "%sx%s" % (width, height)
        width = driver.execute_script("return document.body.scrollWidth")
        details['document_width'][key] = int(width)

    try:
        element = driver.find_element_by_xpath("//meta[@name='viewport']")
        details['viewport_meta_tag'] = element.get_attribute('content')
    except:
        pass

    return details

def check_content(r):
    """
    Adds details to check regarding content of the page

    check: the dict containing details for this URL
    r: requests request/response object
    """
    result = {}

    result['encoding'] = r.encoding
    soup = BeautifulSoup(r.text, 'html.parser')

    result['html'] = r.text

    # page title
    result['title'] = None
    title = soup.find('head').find('title')
    if title is not None:
        result['title'] = normalize_title(title.get_text())

    # canonical link
    result['canonical_link'] = None
    link = soup.find('link', rel='canonical')
    if link:
        result['canonical_link'] = urljoin(r.url, link.get('href'))

    # icon
    result['icon'] = None
    link = soup.find('link', rel=lambda x: x and x.lower()=='icon')
    if link:
        result['icon'] = urljoin(r.url, link.get('href'))
    else:
        link = soup.find('link', rel=lambda x: x and x.lower()=='shortcut icon')
        if link:
            result['icon'] = urljoin(r.url, link.get('href'))

    # feed links
    result['feeds'] = []
    rss_links = soup.find_all('link', type='application/rss+xml')
    atom_links = soup.find_all('link', type='application/atom+xml')

    if len(rss_links) > 0:
        for l in rss_links:
            result['feeds'].append(urljoin(r.url, l.get('href')))
    if len(atom_links) > 0:
        for l in rss_links:
            result['feeds'].append(urljoin(r.url, l.get('href')))

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


def collect_ipv4_addresses(hostname_dict):
    """
    Return list of unique IPv4 addresses
    """
    ips = set()
    for item in hostname_dict.values():
        if 'ip_addresses' not in item:
            continue
        for ip in item['ip_addresses']:
            ips.add(ip)
    return sorted(list(ips))


def parse_generator(generator):
    """
    Return well known CMS names from generator
    """
    generator = generator.lower()
    if 'typo3' in generator:
        return "typo3"
    elif 'wordpress' in generator:
        return "wordpress"
    elif 'drupal' in generator:
        return "drupal"
    elif 'joomla' in generator:
        return "joomla"
    return generator

def check_site(entry):
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

    # all the info we'll return for the site
    result = {
        # input_url: The URL we derived all checks from
        'input_url': entry['url'],
        # Meta: Regional and type metadata for the site
        'meta': {
            'level': entry['level'],
            'state': entry['state'],
            'district': entry['district'],
            'city': entry['city'],
        },
        # Details: All details we collected about the site (which aren't directly related to the report criteria)
        'details': {
            'hostnames': {},
            'ipv4_addresses': [],
            'resolvable_urls': [],
            'canonical_urls': [],
            'urlchecks': [],
            'icons': [],
            'feeds': [],
            'cms': None,
            'responsive': None,
        },
        # The actual report criteria
        'result': {
            'DNS_RESOLVABLE_IPV4': {'type': 'boolean', 'value': False, 'score': 0},
            'SITE_REACHABLE': {'type': 'boolean', 'value': False, 'score': 0},
            'HTTPS': {'type': 'boolean', 'value': False, 'score': 0},
            'WWW_OPTIONAL': {'type': 'boolean', 'value': False, 'score': 0},
            'CANONICAL_URL': {'type': 'boolean', 'value': False, 'score': 0},
            'FAVICON': {'type': 'boolean', 'value': False, 'score': 0},
            'FEEDS': {'type': 'boolean', 'value': False, 'score': 0},
            'HTTP_RESPONSE_DURATION': {'type': 'number', 'value': None, 'score': 0},
            'RESPONSIVE': {'type': 'boolean', 'value': False, 'score': 0},
        },
        'score': 0.0,
    }

    # derive hostnames to test (with/without www.)
    parsed = urlparse(entry['url'])
    hostnames = derive_test_hostnames(parsed.hostname)

    # try to resolve hostnames
    processed_hostnames = {}
    for hn in hostnames:

        processed_hostnames[hn] = {
            'resolvable': False,
        }

        try:
            hostname, aliases, ip_addresses = gethostbyname_ex(hn)
            processed_hostnames[hn]['resolvable'] = True
            processed_hostnames[hn]['resolved_hostname'] = hostname
            processed_hostnames[hn]['aliases'] = aliases
            processed_hostnames[hn]['ip_addresses'] = ip_addresses
        except:
            pass

    result['details']['hostnames'] = processed_hostnames

    result['details']['ipv4_addresses'] = collect_ipv4_addresses(processed_hostnames)

    # check basic HTTP(S) reachability
    checked_urls = []
    checked_urls_set = set()

    for hn in processed_hostnames.keys():

        item = processed_hostnames[hn]

        if not item['resolvable']:
            continue

        for scheme in ('http', 'https'):

            url = scheme + '://' + item['resolved_hostname'] + '/'

            if url in checked_urls_set:
                continue

            checked_urls_set.add(url)

            record = {
                'url': url,
                'error': None,
                'redirects_to': None,
            }

            try:
                r = requests.head(record['url'], headers=headers, allow_redirects=True)
                if r.url == url:
                    logging.info("URL: %s - status %s" % (record['url'], r.status_code))
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

    result['details']['resolvable_urls'] = sorted(checked_urls, key=lambda url: url['url'])
    result['details']['canonical_urls'] = sorted(reduce_urls(checked_urls))

    # Deeper test for the remaining (canonical) URL(s)
    for check_url in result['details']['canonical_urls']:

        logging.info("Downloading URL %s" % check_url)

        check = {
            'url': check_url,
            'status_code': None,
            'duration': None,
            'error': None,
            'content': None,
            'responsive': None,
        }

        try:
            r = requests.get(check_url, headers=headers, timeout=(connect_timeout, read_timeout))
            check['status_code'] = r.status_code
            check['duration'] = round(r.elapsed.microseconds / 1000)

            # Content checks
            if r.status_code < 300:
                check['content'] = check_content(r)

            # Responsiveness check
            try:
                check['responsive'] = check_responsiveness(check_url)
            except Exception as e:
                logging.error("Error when checking responsiveness for '%s': %s" % (check_url, e))

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

        result['details']['urlchecks'].append(check)


    result['details']['urlchecks'] = sorted(result['details']['urlchecks'], key=lambda url: url['url'])

    # collect icons
    icons = set()
    for c in result['details']['urlchecks']:
        if 'content' not in c:
            continue
        if c['content'] is None:
            logging.warning("No content for %s" % entry['url'])
            continue
        if c['content']['icon'] is not None:
            icons.add(c['content']['icon'])
    result['details']['icons'] = sorted(list(icons))

    # collect feeds
    feeds = set()
    for c in result['details']['urlchecks']:
        if c['content'] is None:
            logging.warning("No content for %s" % entry['url'])
            continue
        if 'feeds' in c['content'] and len(c['content']['feeds']):
            for feed in c['content']['feeds']:
                feeds.add(feed)
    result['details']['feeds'] = sorted(list(feeds))

    # detect responsive
    viewports = set()
    min_width = 2000
    for c in result['details']['urlchecks']:
        if c['responsive'] is None:
            continue
        if c['responsive']['viewport_meta_tag'] is not None:
            viewports.add(c['responsive']['viewport_meta_tag'])
        widths = c['responsive']['document_width'].values()
        if min(widths) < min_width:
            min_width = min(widths)
    result['details']['responsive'] = {
        'viewport_meta_tag': list(viewports),
        'min_width': min_width,
    }

    # detect CMS
    for c in result['details']['urlchecks']:
        if c['content'] is None:
            continue
        if 'generator' not in c['content']:
            continue
        if c['content']['generator'] != "" and c['content']['generator'] is not None:

            result['details']['cms'] = parse_generator(c['content']['generator'])
            # Qualify certain CMS flavours in more detail
            if result['details']['cms'] == "typo3":
                if gcms_ip in result['details']['ipv4_addresses']:
                    result['details']['cms'] = "typo3-gcms"
                elif 'typo3-gruene.de' in c['content']['html']:
                    result['details']['cms'] = "typo3-gruene"
            elif result['details']['cms'] == "wordpress":
                if 'Urwahl3000' in c['content']['html']:
                    result['details']['cms'] = "wordpress-urwahl"

        else:
            # No generator Tag. Use HTML content.
            if 'Urwahl3000' in c['content']['html']:
                result['details']['cms'] = "wordpress-urwahl"
            elif 'wordpress' in c['content']['html']:
                result['details']['cms'] = "wordpress"

        # we can stop here
        break


    ### Derive criteria

    # DNS_RESOLVABLE_IPV4
    if len(result['details']['ipv4_addresses']):
        result['result']['DNS_RESOLVABLE_IPV4'] = {'value': True, 'score': 1}

    # SITE_REACHABLE
    for item in result['details']['resolvable_urls']:
        if item['error'] is None:
            result['result']['SITE_REACHABLE'] = {'value': True, 'score': 1}
            break

    # HTTPS
    for item in result['details']['urlchecks']:
        if item['error'] is None and item['url'].startswith('https://'):
            result['result']['HTTPS'] = {'value': True, 'score': 2}
            break

    # WWW_OPTIONAL
    num_hostnames = 0
    for hn in result['details']['hostnames'].keys():
        item = result['details']['hostnames'][hn]
        if not item['resolvable']:
            continue
        num_hostnames += 1
    if num_hostnames > 1:
        result['result']['WWW_OPTIONAL'] = {'value': True, 'score': 1}

    # CANONICAL_URL
    # - either there is only one canonical URL (through redirects)
    # - or several pages have identical rel=canonical links
    if len(result['details']['canonical_urls']) == 1:
        result['result']['CANONICAL_URL'] = {'value': True, 'score': 1}
    else:
        links = set()
        if result['details']['urlchecks'] is None:
            logging.warning("No urlchecks for %s" % entry['url'])
        else:
            for item in result['details']['urlchecks']:
                if item['content']['canonical_link'] is not None:
                    links.add(item['content']['canonical_link'])
        if len(links) == 1:
            result['result']['CANONICAL_URL'] = {'value': True, 'score': 1}

    # FAVICON
    if len(result['details']['icons']):
        result['result']['FAVICON'] = {'value': True, 'score': 1}

    # FEEDS
    if len(result['details']['feeds']):
        result['result']['FEEDS'] = {'value': True, 'score': 1}

    # HTTP_RESPONSE_DURATION
    durations = []
    for item in result['details']['urlchecks']:
        if item['error'] is None:
            durations.append(item['duration'])
    val = round(statistics.mean(durations))
    result['result']['HTTP_RESPONSE_DURATION']['value'] = val
    if val < 100:
        result['result']['HTTP_RESPONSE_DURATION']['score'] = 1
    elif val < 1000:
        result['result']['HTTP_RESPONSE_DURATION']['score'] = 0.5

    # RESPONSIVE
    if result['details']['responsive'] is not None:
        if (result['details']['responsive']['min_width'] < 500 and
            len(result['details']['responsive']['viewport_meta_tag']) > 0):
            result['result']['RESPONSIVE']['value'] = True
            result['result']['RESPONSIVE']['score'] = 1

    # Overall score
    for item in result['result'].keys():
        result['score'] += result['result'][item]['score']

    # clean up - remove full HTML
    for item in result['details']['urlchecks']:
        try:
            del item['content']['html']
        except:
            pass

    return result


def main():
    """
    Bringing it all together
    """
    logging.basicConfig(level=logging.INFO)
    logging.getLogger("urllib3").setLevel(logging.CRITICAL)

    # refresh our local clone of the green directory
    get_green_directory()

    # build the list of website URLs to run checks for
    logging.info("Processing green-directory")
    input_entries = []

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
            input_entries.append({
                "url": website_url,
                "level": entry.get("level"),
                "state": entry.get("state"),
                "district": entry.get("district"),
                "city": entry.get("city"),
            })


    # randomize order, to distribute requests over servers
    logging.info("Shuffling input URLs")
    random.seed()
    random.shuffle(input_entries)

    # run checks
    logging.info("Starting checks")
    results = {}

    pool = Pool(concurrency)
    for ientry in input_entries:
        logging.info("Submitting %s to job pool" % ientry['url'])
        results[ientry['url']] = pool.apply_async(check_site, kwds={'entry': ientry})
    pool.close()
    pool.join()

    logging.info("Checks are finished")

    # Restructure result from dict of ApplyResult
    # to list of dicts and sort in stable way
    json_result = []
    done = set()

    logging.info("Restructuring results")

    # convert results from ApplyResult to dict
    for url in sorted(results.keys()):
        if url not in done:
            logging.info("Getting result for %s" % url)
            try:
                resultsitem = results[url].get()
                json_result.append(resultsitem)
            except Exception as e:
                logging.error("Error getting result for '%s': %s" % (url, e))
        done.add(url)

    # Write result as JSON
    output_filename = os.path.join(result_path, "spider_result.json")
    with open(output_filename, 'w', encoding="utf8") as jsonfile:
        json.dump(json_result, jsonfile, indent=2, sort_keys=True, ensure_ascii=False)


if __name__ == "__main__":
    main()
