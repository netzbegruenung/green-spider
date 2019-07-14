"""
This check attempts to resolve all hostnames/domains in the input URLs.

URLs which are not resolvable are removed from the config.
"""

import logging
from urllib.parse import urlparse
from urllib.parse import urlunparse

import dns.resolver

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

            # remove URL if IPv4 non-resolvable
            if not results[url]['resolvable_ipv4']:
                self.config.remove_url(url)

        return results

    def resolve_hostname(self, hostname):
        """
        Resolve one to IPv4 address(es)
        """
        result = {
            'hostname': hostname,
            'resolvable_ipv4': False,
            'resolvable_ipv6': False,
            'aliases': [],
            'ipv4_addresses': [],
            'ipv6_addresses': [],
        }

        # IPv4
        try:
            answers = dns.resolver.query(hostname, "A")
            result['resolvable_ipv4'] = True
            for rdata in answers:
                result['ipv4_addresses'].append(rdata.address)
        except Exception as e:
            logging.debug("Hostname %s not resolvable via IPv4. Exception: %r" % (hostname, e))

        # IPv6
        try:
            answers = dns.resolver.query(hostname, "AAAA")
            result['resolvable_ipv6'] = True
            for rdata in answers:
                result['ipv6_addresses'].append(rdata.address)
        except Exception as e:
            logging.debug("Hostname %s not resolvable via IPv4. Exception: %r" % (hostname, e))
        
        return result
