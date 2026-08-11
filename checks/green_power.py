"""
This check looks up the domain of site against the Green Web Foundation API,
to confirm that sites in the green party, run on green power, rather
than fossil fuels.
"""

import logging

import requests
from urllib.parse import urlparse

from checks.abstract_checker import AbstractChecker

logger = logging.getLogger(__name__)


class Checker(AbstractChecker):

    API_ENDPOINT = "http://api.thegreenwebfoundation.org/greencheck/"

    def __init__(self, config, previous_results=None):
        super().__init__(config, previous_results)

    def run(self):
        """Executes the check routine, returns result dict"""

        results = {}

        urls = list(self.config.urls)
        for url in urls:
            hostname = urlparse(url).hostname
            results[url] = self.check_for_green_power(hostname)

        return results

    def check_for_green_power(self, url):
        """
        Checks the url passed in agains the Green web Foundation API
        to see if the domain known to be running on green power.
        """
        # use the "big tarp" to catch the error, but don't crash the program
        # returning false because we didn't come back with any  evidence that
        # the site uses green power
        # more on the big tarp:
        # https://www.loggly.com/blog/exceptional-logging-of-exceptions-in-python/
        check_url = f"{self.API_ENDPOINT}{url}"

        try:
            result = requests.get(check_url)
            return result.json().get('green')
        except Exception:
            logger.exception("Requesting data from the API failed")

            return False


