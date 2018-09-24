"""
The checks module contains the individual checks we perform with a page
"""

import logging

from checks import subdomain_variations
#from checks import home_url_canonicalization
#from checks import http_and_https

from checks.config import Config


def perform_checks(input_url):
    """
    Executes the tests in the right order
    """
    check_modules = [
        ('subdomain_variations', subdomain_variations),
        #("home_url_canonicalization", home_url_canonicalization),
        #("http_and_https", http_and_https),
    ]

    result = {}

    config = Config(urls=[input_url])

    for check_name, check in check_modules:
        checker = check.Checker(config)
        result[check_name] = checker.run()

        # update config for the next check
        config = checker.config
    
    return result
