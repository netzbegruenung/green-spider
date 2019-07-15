import unittest
import logging
import sys
from pprint import pprint

from checks import dns_resolution
from checks.config import Config

class TestDNSResolution(unittest.TestCase):

    def runTest(self):
        """Resolves www.google.com"""
        url = 'https://www.google.com/'
        config = Config(urls=[url])
        checker = dns_resolution.Checker(config=config, previous_results={})
        result = checker.run()

        self.assertIn(url, result)
        self.assertEqual(result[url]['hostname'], 'www.google.com')
        self.assertTrue(result[url], 'resolvable_ipv4')
        self.assertTrue(result[url], 'resolvable_ipv6')
        self.assertIsInstance(result[url]['ipv4_addresses'], list)
        self.assertNotEqual(result[url]['ipv4_addresses'], [])

if __name__ == '__main__':
    logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)
    unittest.TextTestRunner().run(TestDNSResolution())

    #unittest.main()
