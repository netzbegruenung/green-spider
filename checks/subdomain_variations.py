"""
This check makes sure that commmonly used variations of a (sub)domain are resolvable.

Example: input_url = 'http://example.com'
         will check: ['example.com', 'www.example.com']

Resolvable subdomains are added to config.urls.

Details on the resolution are returns as a result from the run() method.
"""

import logging
from socket import gethostbyname_ex
from urllib.parse import urlparse

from checks.abstract_checker import AbstractChecker

class Checker(AbstractChecker):
    def __init__(self, config):
        super().__init__(config)

    def run(self):
        """Executes the check routine, returns result dict"""
        logging.debug("subdomain_variations.Checker.run() called with Config: %r" % self.config)
        
        hostnames = self.expand_hostnames()
        
        results = self.resolve_hostnames(hostnames)

        # pass resolvable hostnames on as URLs for further checks
        for item in results:
            if item['resolvable']:
                self.config.add_url('http://%s/' % item['hostname'])

        return results


    def expand_hostnames(self):
        """
        Create variations of subdomains
        """
        hostnames = set()

        for url in self.config.urls:
            parsed = urlparse(url)
            hostnames.add(parsed.hostname)
            if parsed.hostname.startswith('www.'):
                # remove 'www.' prefix
                hostnames.add(parsed.hostname[4:])
            else:
                # add 'www.' prefix
                hostnames.add('www.' + parsed.hostname)

        return sorted(list(hostnames))
    

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


    def resolve_hostnames(self, hostnames):
        result = []
        for hostname in hostnames:
            result.append(self.resolve_hostname(hostname))
        
        return result
