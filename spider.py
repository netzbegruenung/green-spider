"""
Provides the spider functionality (website checks).
"""

import argparse
import json
import logging
import re
import statistics
import time
from datetime import datetime
from pprint import pprint

from google.api_core.exceptions import InvalidArgument
from google.cloud import datastore

import checks
import config
import jobs
import rating

DATASTORE_CLIENT = None


def check_and_rate_site(entry):
    """
    Performs our site check and returns results as a dict.

    1. Normalize the input URL and derive the URLs to check for
    2. HEAD the check urls
    3. Determine the canonical URL
    4. Run full check on canonical URL
    """

    # all the info we'll return for the site
    result = {
        # input_url: The URL we derived all checks from
        'input_url': entry['url'],
        # Meta: Regional and type metadata for the site
        'meta': {
            'type': entry.get('type'),
            'level': entry.get('level'),
            'state': entry.get('state'),
            'district': entry.get('district'),
            'city': entry.get('city'),
        },
        # checks: Results from our checks
        'checks': {},
        # The actual report scoring criteria
        'rating': {},
        # resulting score
        'score': 0.0,
    }

    # Results from our next generation checkers
    result['checks'] = checks.perform_checks(entry['url'])

    result['rating'] = rating.calculate_rating(result['checks'])

    # Overall score is the sum of the individual scores
    for key in result['rating']:
        result['score'] += result['rating'][key]['score']

    # remove full HTML page content,
    # as it's no longer needed
    try:
        for url in result['checks']['page_content']:
            del result['checks']['page_content'][url]['content']
    except:
        pass

    return result


def work_of_queue():
    """
    Take job from queue and finish it until there are no more jobs
    """
    while True:
        job = jobs.get_job_from_queue(DATASTORE_CLIENT)
        if job is None:
            logging.info("No more jobs. Exiting.")
            break

        logging.info("Starting job %s", job["url"])
        result = check_and_rate_site(entry=job)

        logging.debug("Full JSON representation of returned result: %s", json.dumps(result))

        logging.info("Job %s finished checks", job["url"])
        logging.info("Job %s writing to DB", job["url"])

        key = DATASTORE_CLIENT.key(config.RESULTS_DATASTORE_KIND, job["url"])
        entity = datastore.Entity(key=key, exclude_from_indexes=['results'])
        record = {
            'created': datetime.utcnow(),
            'meta': result['meta'],
            'checks': result['checks'],
            'rating': result['rating'],
            'score': result['score'],
        }
        entity.update(record)
        try:
            DATASTORE_CLIENT.put(entity)
        except InvalidArgument as ex:
            logging.error("Could not write result: %s", ex)
        except Exception as ex:
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
        jobs.create_jobs(DATASTORE_CLIENT, args.url)
    else:
        work_of_queue()
