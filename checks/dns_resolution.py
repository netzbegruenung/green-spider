"""
This check attempts to resolve all hostnames/domains in the input URLs.

URLs which are not resolvable are removed from the config.
"""

import logging
from socket import gethostbyname_ex
from urllib.parse import urlparse
from urllib.parse import urlunparse

from checks.abstract_checker import AbstractChecker


class Checker(AbstractChecker):
    def __init__(self, config, previous_results=None):
        super().__init__(config, previous_results)

    def run(self):
        """Executes the check routine, returns result dict"""
        
        results = {}

        urls = list(self.config.urls)
        for url in urls:
            parsed = urlparse(url)
            
            results[url] = self.resolve_hostname(parsed.hostname)

            # remove URL if non-resolvable
            if not results[url]['resolvable']:
                self.config.remove_url(url)

        return results

    def resolve_hostname(self, hostname):
        """
        Resolve one to IPv4 address(es)
        """
        result = {
            'hostname': hostname,
            'resolvable': False,
            'aliases': [],
            'ipv4_addresses': [],
        }

        try:
            hostname, aliases, ipv4_addresses = gethostbyname_ex(hostname)
            result['resolvable'] = True
            result['aliases'] = aliases
            result['ipv4_addresses'] = ipv4_addresses
        except Exception as e:
            logging.debug("Hostname %s not resolvable. Exception: %r" % (hostname, e))
        
        return result
