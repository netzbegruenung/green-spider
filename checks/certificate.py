"""
Gathers information on the TLS/SSL certificate used by a server
"""

from urllib.parse import urlparse
import logging
import ssl
from datetime import datetime
from datetime import timezone

from OpenSSL import crypto

from checks.abstract_checker import AbstractChecker

class Checker(AbstractChecker):
    def __init__(self, config, previous_results=None):
        super().__init__(config, previous_results)
    
    def run(self):
        results = {}

        for url in self.config.urls:
            if url.startswith('https://'):
                results[url] = self.get_certificate(url)

        return results
    
    def get_certificate(self, url):
        result = {
            'exception': None,
            'serial_number': None,
            'subject': None,
            'issuer': None,
            'not_before': None,
            'not_after': None
        }

        parsed = urlparse(url)
        try:
            cert = ssl.get_server_certificate((parsed.hostname, 443))
            x509 = crypto.load_certificate(crypto.FILETYPE_PEM, cert)
            result['serial_number'] = str(x509.get_serial_number())

            nb = x509.get_notBefore().decode('utf-8')
            na = x509.get_notAfter().decode('utf-8')
            
            # parse '2018 06 27 00 00 00Z'
            result['not_before'] = datetime(int(nb[0:4]), int(nb[4:6]), int(nb[6:8]), int(nb[8:10]), int(nb[10:12]), int(nb[12:14]), tzinfo=timezone.utc).isoformat()
            result['not_after']  = datetime(int(na[0:4]), int(na[4:6]), int(na[6:8]), int(na[8:10]), int(na[10:12]), int(na[12:14]), tzinfo=timezone.utc).isoformat()

            # decode and convert from bytes to unicode
            result['subject'] = dict([tuple(map(lambda x: x.decode('utf-8'), tup)) for tup in x509.get_subject().get_components()])
            result['issuer']  = dict([tuple(map(lambda x: x.decode('utf-8'), tup)) for tup in x509.get_issuer().get_components()])
            
        except Exception as e:
            result['exception'] = {
                'type': str(type(e)),
                'message': str(e),
            }
            logging.warning("Error when getting certificate for %s: %r" % (url, e))

        return result
