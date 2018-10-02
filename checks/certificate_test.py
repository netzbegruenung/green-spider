from checks import certificate
from checks.config import Config
import unittest

class TestCertificateChecker(unittest.TestCase):

    def test_google(self):
        url = 'https://www.google.com/'
        config = Config(urls=[url])
        checker = certificate.Checker(config=config, previous_results={})
        result = checker.run()
        self.assertIn(url, result)
        self.assertIsNone(result[url]['exception'])
        self.assertEqual(result[url]['issuer']['O'], 'Google Trust Services')

    def test_kaarst(self):
        url = 'https://www.gruenekaarst.de/'
        config = Config(urls=[url])
        checker = certificate.Checker(config=config, previous_results={})
        result = checker.run()
        self.assertIn(url, result)
        self.assertIsNone(result[url]['exception'])
        self.assertEqual(result[url]['issuer']['O'], 'COMODO CA Limited')


if __name__ == '__main__':
    unittest.main()
