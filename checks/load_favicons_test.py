from pprint import pprint

import httpretty
from httpretty import httprettified
import unittest

from checks import load_favicons
from checks.config import Config

@httprettified
class TestFavicons(unittest.TestCase):

    def test_favicons(self):
        # This site has a favicon
        url1 = 'http://example1.com/favicon.ico'
        httpretty.register_uri(httpretty.HEAD, url1,
                               body='',
                               adding_headers={
                                   "Content-type": "image/x-ico",
                               })
        
        # This site has no favicon
        url2 = 'http://example2.com/favicon.ico'
        httpretty.register_uri(httpretty.HEAD, url2,
                               status=404,
                               body='Not found',
                               adding_headers={
                                   "Content-type": "text/plain",
                               })


        config = Config(urls=['http://example1.com/path/', 'http://example2.com/'])
        checker = load_favicons.Checker(config=config)

        result = checker.run()
        pprint(result)

        self.assertEqual(result, {
            'http://example1.com/path/': {
                'url': 'http://example1.com/favicon.ico'
            }
        })

