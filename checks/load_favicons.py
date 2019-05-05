"""
Loads /favicon if no icon has been found otherwise
"""

import logging
from time import mktime
from datetime import datetime
from urllib.parse import urlparse

import requests

from checks.abstract_checker import AbstractChecker

class Checker(AbstractChecker):
    def __init__(self, config, previous_results=None):
        super().__init__(config, previous_results)
        self.favicons = {}

    def run(self):
        for url in self.config.urls:
            self.load_favicon(url)

        return self.favicons
    
    def load_favicon(self, url):
        """
        This loads /favicon.ico for the site's URL
        """
        parsed = urlparse(url)
        ico_url = parsed.scheme + "://" + parsed.hostname + "/favicon.ico"
        r = requests.head(ico_url)
        if r.status_code == 200:
            self.favicons[url] = {
                'url': ico_url,
            }
