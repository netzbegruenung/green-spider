from checks import certificate
from checks.config import Config

import unittest
from pprint import pprint

class TestCertificateChecker(unittest.TestCase):

    def test_google(self):
        """Load cert from a site that should work"""
        url = 'https://www.google.com/'
        config = Config(urls=[url])
        checker = certificate.Checker(config=config, previous_results={})
        result = checker.run()
        self.assertIn(url, result)
        self.assertIsNone(result[url]['exception'])
        self.assertEqual(result[url]['issuer']['O'], 'Google Trust Services')

    def test_kaarst(self):
        """Real-workd example"""
        url = 'https://www.gruenekaarst.de/'
        config = Config(urls=[url])
        checker = certificate.Checker(config=config, previous_results={})
        result = checker.run()
        self.assertIn(url, result)
        self.assertIsNone(result[url]['exception'])
        self.assertEqual(result[url]['issuer']['O'], 'Sectigo Limited')

    def test_tls_v_1_0(self):
        """Load a certificate for a TLS v1.0 server"""
        url = 'https://tls-v1-0.badssl.com:1010/'
        config = Config(urls=[url])
        checker = certificate.Checker(config=config, previous_results={})
        result = checker.run()
        self.assertIn(url, result)
        self.assertIsNone(result[url]['exception'])
        self.assertEqual(result[url]['subject']['CN'], '*.badssl.com')

    def test_tls_v_1_1(self):
        """Load a certificate for a TLS v1.1 server"""
        url = 'https://tls-v1-1.badssl.com:1011/'
        config = Config(urls=[url])
        checker = certificate.Checker(config=config, previous_results={})
        result = checker.run()
        self.assertIn(url, result)
        self.assertIsNone(result[url]['exception'])
        self.assertEqual(result[url]['subject']['CN'], '*.badssl.com')

    def test_tls_v_1_2(self):
        """Load a certificate for a TLS v1.2 server"""
        url = 'https://tls-v1-2.badssl.com:1012/'
        config = Config(urls=[url])
        checker = certificate.Checker(config=config, previous_results={})
        result = checker.run()
        self.assertIn(url, result)
        self.assertIsNone(result[url]['exception'])
        self.assertEqual(result[url]['subject']['CN'], '*.badssl.com')



if __name__ == '__main__':
    unittest.main()
