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
import manager
import rating

def check_and_rate_site(entry):
    """
    Performs our site checks, calculates the score
    and returns results as a dict.
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

    # Remove bigger result portions to safe some storage:
    # - HTML page content
    # - Hyperlinks
    # - Performnance log
    try:
        for url in result['checks']['page_content']:
            del result['checks']['page_content'][url]['content']

        for url in result['checks']['load_in_browser']:
            del result['checks']['load_in_browser'][url]['performance_log']

        del result['checks']['hyperlinks']
    except:
        pass

    return result


def test_url(url):
    """
    Run the spider for a single URL and print the result.
    Doesn't write anything to the database.
    """
    logging.info("Crawling URL %s", url)

    # mock job
    job = {
        "url": url,
    }

    result = check_and_rate_site(entry=job)
    pprint(result)


def validate_job(jobdict):
    if "url" not in jobdict:
        raise Exception("Job does not have required 'url' attribute")
