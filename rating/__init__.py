"""
The rating module contains the functionality to get calculate score for certain
criteria based on information gather by checks before.
"""

import logging

from rating import canonical_url
from rating import favicon
from rating import feeds
from rating import https
from rating import reachable
from rating import resolvable
from rating import response_duration
from rating import responsive_layout
from rating import www_optional


def calculate_rating(results):
    """
    Calculates ratings for a number of criteria.

    Params:
    results - Results dictionary from checks
    """

    # The sequence of checks to run. Order is important!
    # Checks which expand the URLs list must come first.
    # After that, dependencies (encoded in the checks) have to be fulfilled.
    rating_modules = [
        ('DNS_RESOLVABLE_IPV4', resolvable),
        ('SITE_REACHABLE', reachable),
        ('HTTPS', https),
        ('WWW_OPTIONAL', www_optional),
        ('CANONICAL_URL', canonical_url),
        ('HTTP_RESPONSE_DURATION', response_duration),
        ('FAVICON', favicon),
        ('FEEDS', feeds),
        ('RESPONSIVE', responsive_layout),
    ]

    output = {}

    for name, mod in rating_modules:

        rater = mod.Rater(results)
        output[name] = rater.rate()

    
    return output
