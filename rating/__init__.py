"""
The rating module contains the functionality to get calculate score for certain
criteria based on information gather by checks before.
"""

import logging

from rating import canonical_url
from rating import contact_link
from rating import favicon
from rating import feeds
from rating import https
from rating import no_network_errors
from rating import no_script_errors
from rating import no_third_party_cookies
from rating import reachable
from rating import resolvable
from rating import response_duration
from rating import responsive_layout
from rating import social_media_links
from rating import use_specific_fonts
from rating import www_optional
from rating import green_power


def calculate_rating(results):
    """
    Calculates ratings for a number of criteria.

    Params:
    results - Results dictionary from checks
    """

    # The raters to execute.
    rating_modules = {
        'CANONICAL_URL': canonical_url,
        'CONTACT_LINK': contact_link,
        'DNS_RESOLVABLE_IPV4': resolvable,
        'FAVICON': favicon,
        'FEEDS': feeds,
        'HTTPS': https,
        'HTTP_RESPONSE_DURATION': response_duration,
        'NO_NETWORK_ERRORS': no_network_errors,
        'NO_SCRIPT_ERRORS': no_script_errors,
        'NO_THIRD_PARTY_COOKIES': no_third_party_cookies,
        'RESPONSIVE': responsive_layout,
        'SITE_REACHABLE': reachable,
        'SOCIAL_MEDIA_LINKS': social_media_links,
        'USE_SPECIFIC_FONTS': use_specific_fonts,
        'WWW_OPTIONAL': www_optional,
        'GREEN_POWER': green_power,
    }

    output = {}

    for name in rating_modules:

        rater = rating_modules[name].Rater(results)
        output[name] = rater.rate()

    return output
