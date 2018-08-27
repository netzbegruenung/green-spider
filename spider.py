"""
Provides the spider functionality (website checks).
"""

import argparse
import json
import logging
import os
import random
import re
import shutil
import statistics
from datetime import datetime
from socket import gethostbyname_ex
from urllib.parse import urljoin
from urllib.parse import urlparse

import requests
import yaml
import tenacity

from bs4 import BeautifulSoup
from git import Repo
from selenium import webdriver
from google.cloud import datastore
from google.api_core.exceptions import Aborted
from google.api_core.exceptions import InvalidArgument


# configuration

# connection timeout for website checks (seconds)
CONNECT_TIMEOUT = 5

# response timeout for website checks
READ_TIMEOUT = 10

# Git repo for our data
GREEN_DIRECTORY_REPO = 'https://github.com/netzbegruenung/green-directory.git'
# folder in that repo that holds the data
GREEN_DIRECTORY_DATA_PATH = 'data/countries/de'
GREEN_DIRECTORY_LOCAL_PATH = './cache/green-directory'

RESULT_PATH = '/out'

# IP address of the newthinking GCMS server
GCMS_IP = "91.102.13.20"

JOB_DATASTORE_KIND = 'spider-jobs'
RESULTS_DATASTORE_KIND = 'spider-results'

# end configuration

DATASTORE_CLIENT = None


def chunks(the_list, size):
    """
    Yield successive n-sized chunks from list the_list
    where n = size.
    """
    for i in range(0, len(the_list), size):
        yield the_list[i:i + size]


def create_jobs(url=None):
    """
    Read all URLs from green directory and fill a job database
    with one job per URL.

    Alternatively, if the url argument is given, only the given URL
    will be added as a spider job.
    """

    # refresh our local clone of the green directory
    logging.info("Refreshing green-directory clone")
    get_green_directory()

    # build the list of website URLs to run checks for
    logging.info("Processing green-directory")
    input_entries = []

    count = 0

    for entry in dir_entries():

        if 'type' not in entry:
            logging.error("Entry without type")
            continue
        if 'urls' not in entry:
            logging.debug("Entry %s does not have any URLs.", repr_entry(entry))
            continue

        website_url = None
        for index in range(len(entry['urls'])):
            try:
                if entry['urls'][index]['type'] == "WEBSITE":
                    website_url = entry['urls'][index]['url']
                    if website_url:
                        if url is not None and website_url != url:
                            continue
                        input_entries.append({
                            "url": website_url,
                            "level": entry.get("level"),
                            "state": entry.get("state"),
                            "district": entry.get("district"),
                            "city": entry.get("city"),
                        })
                        count += 1
            except NameError:
                logging.error("Error in %s: 'url' key missing (%s)",
                              repr_entry(entry), entry['urls'][index])

    # ensure the passed URL argument is really there, even if not part
    # of the directory.
    if url and count == 0:
        logging.info("Adding job for URL %s which is not part of green-directory", url)
        input_entries.append({
            "url": url,
            "level": None,
            "state": None,
            "district": None,
            "city": None,
        })

    # randomize order, to distribute requests over servers
    logging.debug("Shuffling input URLs")
    random.seed()
    random.shuffle(input_entries)

    count = 0
    logging.info("Writing jobs")

    entities = []

    for entry in input_entries:
        key = DATASTORE_CLIENT.key(JOB_DATASTORE_KIND, entry["url"])
        entity = datastore.Entity(key=key)
        entity.update({
            "created": datetime.utcnow(),
            "level": entry["level"],
            "state": entry["state"],
            "district": entry["district"],
            "city": entry["city"],
        })
        entities.append(entity)

    # commmit to DB
    for chunk in chunks(entities, 300):
        logging.debug("Writing jobs chunk of length %d", len(chunk))
        DATASTORE_CLIENT.put_multi(chunk)
        count += len(chunk)

    logging.info("Writing jobs done, %s jobs added", count)


def get_green_directory():
    """
    Clones the source of website URLs, the green directory,
    into the local file system using git
    """
    if os.path.exists(GREEN_DIRECTORY_LOCAL_PATH):
        shutil.rmtree(GREEN_DIRECTORY_LOCAL_PATH)
    Repo.clone_from(GREEN_DIRECTORY_REPO, GREEN_DIRECTORY_LOCAL_PATH)


def dir_entries():
    """
    Iterator over all data files in the cloned green directory
    """
    path = os.path.join(GREEN_DIRECTORY_LOCAL_PATH, GREEN_DIRECTORY_DATA_PATH)
    for root, _, files in os.walk(path):
        for fname in files:

            filepath = os.path.join(root, fname)
            if not filepath.endswith(".yaml"):
                continue

            with open(filepath, 'r', encoding='utf8') as yamlfile:
                for doc in yaml.load_all(yamlfile):
                    yield doc


def repr_entry(entry):
    """
    Return string representation of a directory entry,
    for logging/debugging purposes
    """
    ret = entry['type']
    if 'level' in entry:
        ret += "/" + entry['level']
    if 'state' in entry:
        ret += "/" + entry['state']
    if 'district' in entry:
        ret += "/" + entry['district']
    return ret


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

    return sorted(list(hostnames))


def reduce_urls(urllist):
    """
    Reduce a list of urls with metadata by eliminating those
    that either don't work or lead somewhere else
    """
    targets = set()
    for url in urllist:
        if url['error'] is not None:
            continue
        if url['redirects_to'] is not None:
            targets.add(url['redirects_to'])
        else:
            targets.add(url['url'])
    return sorted(list(targets))


def normalize_title(title):
    """
    Removes garbage from HTML page titles
    """
    title = title.replace(u'\u00a0', ' ')
    title = title.replace('  ', ' ')
    title = title.strip()
    return title


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
        (320, 480), # old smartphone
        (768, 1024), # older tablet or newer smartphone
        (1024, 768), # older desktop or horiz. tablet
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


def check_content(req):
    """
    Adds details to check regarding content of the page

    check: the dict containing details for this URL
    r: requests request/response object
    """
    result = {}

    result['encoding'] = req.encoding.lower()
    soup = BeautifulSoup(req.text, 'html.parser')

    result['html'] = req.text

    # page title
    result['title'] = None
    title = None
    head = soup.find('head')
    if head is not None:
        title = head.find('title')
    if title is not None:
        result['title'] = normalize_title(title.get_text())

    # canonical link
    result['canonical_link'] = None
    link = soup.find('link', rel='canonical')
    if link:
        result['canonical_link'] = urljoin(req.url, link.get('href'))

    # icon
    result['icon'] = None
    link = soup.find('link', rel=lambda x: x and x.lower() == 'icon')
    if link:
        result['icon'] = urljoin(req.url, link.get('href'))
    else:
        link = soup.find('link', rel=lambda x: x and x.lower() == 'shortcut icon')
        if link:
            result['icon'] = urljoin(req.url, link.get('href'))

    # feed links
    result['feeds'] = []
    rss_links = soup.find_all('link', type='application/rss+xml')
    atom_links = soup.find_all('link', type='application/atom+xml')

    if rss_links:
        for link in rss_links:
            result['feeds'].append(urljoin(req.url, link.get('href')))
    if atom_links:
        for link in rss_links:
            result['feeds'].append(urljoin(req.url, link.get('href')))

    # generator meta tag
    result['generator'] = None
    if head is not None:
        generator = head.select('[name=generator]')
        if generator:
            result['generator'] = generator[0].get('content')

    # opengraph meta tags
    result['opengraph'] = None
    opengraph = set()
    if head is not None:
        for item in head.find_all(property=re.compile('^og:')):
            opengraph.add(item.get('property'))
        for item in head.find_all(itemprop=re.compile('^og:')):
            opengraph.add(item.get('itemprop'))
        if opengraph:
            result['opengraph'] = sorted(list(opengraph))

    return result


def collect_ipv4_addresses(hostname_dict):
    """
    Return list of unique IPv4 addresses
    """
    ips = set()
    for item in hostname_dict.values():
        if 'ip_addresses' not in item:
            continue
        for ip_addr in item['ip_addresses']:
            ips.add(ip_addr)
    return sorted(list(ips))


def parse_generator(generator):
    """
    Return well known CMS names from generator
    """
    generator = generator.lower()
    if 'typo3' in generator:
        return "typo3"
    if 'wordpress' in generator:
        return "wordpress"
    if 'drupal' in generator:
        return "drupal"
    if 'joomla' in generator:
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
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_4) ' +
                      'AppleWebKit/537.36 (KHTML, like Gecko) ' +
                      'Chrome/65.0.3325.181 green-spider/0.1'
    }

    # all the info we'll return for the site
    result = {
        # input_url: The URL we derived all checks from
        'input_url': entry['url'],
        # Meta: Regional and type metadata for the site
        'meta': {
            'level': entry.get('level'),
            'state': entry.get('state'),
            'district': entry.get('district'),
            'city': entry.get('city'),
        },
        # Details: All details we collected about the site (which aren't directly
        # related to the report criteria)
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
    for hostname in hostnames:

        processed_hostnames[hostname] = {
            'resolvable': False,
        }

        try:
            hostname, aliases, ip_addresses = gethostbyname_ex(hostname)
            processed_hostnames[hostname]['resolvable'] = True
            processed_hostnames[hostname]['resolved_hostname'] = hostname
            processed_hostnames[hostname]['aliases'] = aliases
            processed_hostnames[hostname]['ip_addresses'] = ip_addresses
        except:
            pass

    result['details']['hostnames'] = processed_hostnames

    result['details']['ipv4_addresses'] = collect_ipv4_addresses(processed_hostnames)

    # check basic HTTP(S) reachability
    checked_urls = []
    checked_urls_set = set()

    for hostname in processed_hostnames.keys():

        item = processed_hostnames[hostname]

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
                req = requests.head(record['url'], headers=headers, allow_redirects=True)
                if req.url == url:
                    logging.info("URL: %s - status %s", record['url'], req.status_code)
                else:
                    logging.info("URL: %s - status %s - redirects to %s", record['url'],
                                 req.status_code, req.url)
                    record['redirects_to'] = req.url
            except Exception as exc:
                record['error'] = {
                    'type': str(type(exc)),
                    'message': str(exc),
                }
                logging.info("URL %s: %s %s", url, str(type(exc)), exc)

            checked_urls.append(record)

    result['details']['resolvable_urls'] = sorted(checked_urls, key=lambda url: url['url'])
    result['details']['canonical_urls'] = sorted(reduce_urls(checked_urls))

    # Deeper test for the remaining (canonical) URL(s)
    for check_url in result['details']['canonical_urls']:

        logging.info("Downloading URL %s", check_url)

        check = {
            'url': check_url,
            'status_code': None,
            'duration': None,
            'error': None,
            'content': None,
            'responsive': None,
        }

        try:
            req = requests.get(check_url, headers=headers, timeout=(CONNECT_TIMEOUT, READ_TIMEOUT))
            check['status_code'] = req.status_code
            check['duration'] = round(req.elapsed.microseconds / 1000)

            # Content checks
            if req.status_code < 300:
                check['content'] = check_content(req)

            # Responsiveness check
            try:
                check['responsive'] = check_responsiveness(check_url)
            except Exception as exc:
                logging.error("Error when checking responsiveness for '%s': %s", check_url, exc)

        except requests.exceptions.ConnectionError as exc:
            logging.error(str(exc) + " " + check_url)
            check['error'] = "connection"
        except requests.exceptions.ReadTimeout as exc:
            logging.error(str(exc) + " " + check_url)
            check['error'] = "read_timeout"
        except requests.exceptions.Timeout as exc:
            logging.error(str(exc) + " " + check_url)
            check['error'] = "connection_timeout"
        except Exception as exc:
            logging.error(str(exc) + " " + check_url)
            check['error'] = "unknown"

        result['details']['urlchecks'].append(check)


    result['details']['urlchecks'] = sorted(result['details']['urlchecks'],
                                            key=lambda url: url['url'])

    # collect icons
    icons = set()
    for c in result['details']['urlchecks']:
        if 'content' not in c:
            continue
        if c['content'] is None:
            logging.warning("No content for %s", entry['url'])
            continue
        if c['content']['icon'] is not None:
            icons.add(c['content']['icon'])
    result['details']['icons'] = sorted(list(icons))

    # collect feeds
    feeds = set()
    for c in result['details']['urlchecks']:
        if c['content'] is None:
            logging.warning("No content for %s", entry['url'])
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
                if GCMS_IP in result['details']['ipv4_addresses']:
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
            elif ('josephknowsbest' in c['content']['html'] or
                  'Joseph-knows-best' in c['content']['html']):
                result['details']['cms'] = "wordpress-josephknowsbest"
            elif 'wordpress' in c['content']['html']:
                result['details']['cms'] = "wordpress"

        # we can stop here
        break


    ### Derive criteria

    # DNS_RESOLVABLE_IPV4
    if result['details']['ipv4_addresses']:
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
    for hostname in result['details']['hostnames'].keys():
        item = result['details']['hostnames'][hostname]
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
            logging.warning("No urlchecks for %s", entry['url'])
        else:
            for item in result['details']['urlchecks']:
                if item['content'] is not None and item['content']['canonical_link'] is not None:
                    links.add(item['content']['canonical_link'])
        if len(links) == 1:
            result['result']['CANONICAL_URL'] = {'value': True, 'score': 1}

    # FAVICON
    if result['details']['icons']:
        result['result']['FAVICON'] = {'value': True, 'score': 1}

    # FEEDS
    if result['details']['feeds']:
        result['result']['FEEDS'] = {'value': True, 'score': 1}

    # HTTP_RESPONSE_DURATION
    durations = []
    for item in result['details']['urlchecks']:
        if item['error'] is None:
            durations.append(item['duration'])
    if durations:
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


@tenacity.retry(wait=tenacity.wait_exponential(),
                retry=tenacity.retry_if_exception_type(Aborted))
def get_job_from_queue():
    """
    Returns a URL from the queue
    """
    out = None

    with DATASTORE_CLIENT.transaction():
        query = DATASTORE_CLIENT.query(kind=JOB_DATASTORE_KIND)
        for entity in query.fetch(limit=1):
            logging.debug("Got job: %s", entity)
            out = dict(entity)
            out["url"] = entity.key.name
            DATASTORE_CLIENT.delete(entity.key)

    return out

def work_of_queue():
    """
    Take job from queue and finish it until there are no more jobs
    """
    while True:
        job = get_job_from_queue()
        if job is None:
            logging.info("No more jobs. Exiting.")
            break

        logging.info("Starting job %s", job["url"])
        result = check_site(entry=job)
        #logging.debug(result)
        logging.info("Job %s finished checks", job["url"])
        logging.info("Job %s writing to DB", job["url"])

        key = DATASTORE_CLIENT.key(RESULTS_DATASTORE_KIND, job["url"])
        entity = datastore.Entity(key=key, exclude_from_indexes=['results'])
        record = {
            "created": datetime.utcnow(),
            "results": result,
        }
        entity.update(record)
        try:
            DATASTORE_CLIENT.put(entity)
        except InvalidArgument as ex:
            logging.error("Could not write result: %s", ex)
        except ex:
            logging.error("Could not write result: %s", ex)


if __name__ == "__main__":
    """
    Bringing it all together
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('--credentials-path', dest='credentials_path',
                        help='Path to the service account credentials JSON file',
                        default='/secrets/service-account.json')
    parser.add_argument('--loglevel', help="error, warn, info, or debug (default: info)",
                        default='info')

    subparsers = parser.add_subparsers(help='sub-command help', dest='command')

    subparsers.add_parser('spider', help='Take jobs off the queue and spider')

    jobs_parser = subparsers.add_parser('jobs', help='Create jobs for the queue')

    jobs_parser.add_argument('--url', help='Add a job to spider a URL')
    args = parser.parse_args()

    loglevel = args.loglevel.lower()
    if loglevel == 'error':
        logging.basicConfig(level=logging.ERROR)
    elif loglevel == 'warn':
        logging.basicConfig(level=logging.WARN)
    elif loglevel == 'debug':
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)
        loglevel = 'info'

    logging.getLogger("urllib3").setLevel(logging.CRITICAL)

    DATASTORE_CLIENT = datastore.Client.from_service_account_json(args.credentials_path)

    logging.debug("Called command %s", args.command)

    if args.command == 'jobs':
        create_jobs(args.url)
    else:
        work_of_queue()
