import httpretty
from httpretty import httprettified
import unittest

from checks import url_reachability
from checks.config import Config

@httprettified
class TestCharsetChecker(unittest.TestCase):

    def test_success(self):
        url = 'http://www.example.com/'
        httpretty.register_uri(httpretty.HEAD, url,
            status=200, body="<html></html>")

        config = Config(urls=[url])
        checker = url_reachability.Checker(config=config, previous_results={})
        result = checker.run()

        self.assertEqual(result[url]['url'], url)
        self.assertEqual(result[url]['redirect_history'], [])
        self.assertEqual(result[url]['status'], 200)
        self.assertIsNone(result[url]['exception'])
        self.assertTrue(0 < result[url]['duration'] < 300)


    def test_redirect(self):
        url = 'http://www.example.com/'
        url2 = 'http://www2.example.com/'
        httpretty.register_uri(httpretty.HEAD, url,
            status=302, body="",
            adding_headers={"Location": url2})
        httpretty.register_uri(httpretty.HEAD, url2,
            status=200, body="<html></html>")

        config = Config(urls=[url])
        checker = url_reachability.Checker(config=config, previous_results={})
        result = checker.run()

        self.assertIn(url, result)
        self.assertEqual(result[url]['url'], url)
        self.assertEqual(result[url]['status'], 200)
        self.assertIsNone(result[url]['exception'])
        self.assertTrue(0 < result[url]['duration'] < 100)
        self.assertEqual(len(result[url]['redirect_history']), 1)
        self.assertEqual(result[url]['redirect_history'][0]['status'], 302)
        self.assertEqual(result[url]['redirect_history'][0]['redirect_to'], url2)


    def test_notfound(self):
        url = 'http://www.example.com/'
        httpretty.register_uri(httpretty.HEAD, url,
            status=404, body="<html><body>Not found</body></html>")

        config = Config(urls=[url])
        checker = url_reachability.Checker(config=config, previous_results={})
        result = checker.run()

        self.assertEqual(result[url]['url'], url)
        self.assertEqual(result[url]['redirect_history'], [])
        self.assertEqual(result[url]['status'], 404)
        self.assertIsNone(result[url]['exception'])

        newconfig = checker.config

        self.assertEqual(len(newconfig.urls), 0)



if __name__ == '__main__':
    unittest.main()
