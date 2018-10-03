import unittest
from pprint import pprint

from checks import domain_variations
from checks.config import Config


class TestDomainVariations(unittest.TestCase):

    def test_simple(self):
        url = 'http://example.org/'
        config = Config(urls=[url])
        checker = domain_variations.Checker(config=config, previous_results={})
        checker.run()
        config_after = checker.config

        self.assertEqual(config_after.urls, ['http://example.org/', 'http://www.example.org/'])

if __name__ == '__main__':
    unittest.main()
