"""
This adds commonly tried variations of domains/subdomains to the URLs config.
"""

import logging

from urllib.parse import urlparse
from urllib.parse import urlunparse

from checks.abstract_checker import AbstractChecker


class Checker(AbstractChecker):
    def __init__(self, config, previous_results=None):
        super().__init__(config, previous_results)

    def run(self):        
        urls = list(self.config.urls)
        for url in urls:
            parsed = urlparse(url)
            hostnames = self.expand_hostname(parsed.hostname)
            
            for hostname in hostnames:
                self.config.add_url(urlunparse((parsed.scheme, hostname, 
                    parsed.path, parsed.params, parsed.query, parsed.fragment)))

        return None


    def expand_hostname(self, hostname):
        """
        Create variations of subdomains
        """
        hostnames = set()

        hostnames.add(hostname)
        if hostname.startswith('www.'):
            # remove 'www.' prefix
            hostnames.add(hostname[4:])
        else:
            # add 'www.' prefix
            hostnames.add('www.' + hostname)

        return sorted(list(hostnames))
