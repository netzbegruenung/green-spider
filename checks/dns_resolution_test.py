import unittest
from pprint import pprint

from checks import dns_resolution
from checks.config import Config

class TestDNSResolution(unittest.TestCase):

    def test_google(self):
        """Resolves www.google.com"""
        url = 'https://www.google.com/'
        config = Config(urls=[url])
        checker = dns_resolution.Checker(config=config, previous_results={})
        result = checker.run()

        self.assertIn(url, result)
        self.assertEqual(result[url]['hostname'], 'www.google.com')
        self.assertTrue(result[url], 'resolvable')
        self.assertIsInstance(result[url]['ipv4_addresses'], list)
        self.assertNotEqual(result[url]['ipv4_addresses'], [])

if __name__ == '__main__':
    unittest.main()
