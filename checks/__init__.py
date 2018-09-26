"""
The checks module contains the functionality to get information and test certain
functionality of a site or individual pages.
"""

import logging

from checks import charset
from checks import dns_resolution
from checks import duplicate_content
from checks import domain_variations
from checks import generator
from checks import html_head
from checks import http_and_https
from checks import page_content
from checks import responsive_layout
from checks import url_reachability
from checks import url_canonicalization

from checks.config import Config


def perform_checks(input_url):
    """
    Executes all our URL/site checks and returns a big-ass result dict.
    """

    # The sequence of checks to run. Order is important!
    # Checks which expand the URLs list must come first.
    # After that, dependencies (encoded in the checks) have to be fulfilled.
    check_modules = [
        ('domain_variations', domain_variations),
        ('http_and_https', http_and_https),
        ('dns_resolution', dns_resolution),
        ('url_reachability', url_reachability),
        ('url_canonicalization', url_canonicalization),
        ('page_content', page_content),
        ('duplicate_content', duplicate_content),
        ('charset', charset),
        ('html_head', html_head),
        ('generator', generator),
        ('responsive_layout', responsive_layout),
    ]

    results = {}

    config = Config(urls=[input_url],
        user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) ' +
                   'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100 ' +
                   'Safari/537.36 green-spider/0.2')

    for check_name, check in check_modules:
        checker = check.Checker(config=config,
                                previous_results=results)
        result = checker.run()
        results[check_name] = result

        # update config for the next check
        config = checker.config
        logging.debug("config after check %s: %r" % (check_name, config))
    
    return results
