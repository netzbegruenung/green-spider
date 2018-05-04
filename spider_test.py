import unittest
import requests
import responses
import spider


class TestDeriveHostnames(unittest.TestCase):

    def test_basic1(self):
        hn = spider.derive_test_hostnames('www.my-domain.de')
        expected = ['my-domain.de', 'www.my-domain.de']
        self.assertEqual(hn, expected)

    def test_basic2(self):
        hn = spider.derive_test_hostnames('domain.de')
        expected = ['domain.de', 'www.domain.de']
        self.assertEqual(hn, expected)


class TestReduceURLs(unittest.TestCase):

    def test_basic(self):
        testdata = [
            {'url': 'one', 'error': None, 'redirects_to': None},
            {'url': 'two', 'error': 'Yes', 'redirects_to': None},
            {'url': 'three', 'error': None, 'redirects_to': 'five'},
        ]
        expected_result = ['five', 'one']
        result = spider.reduce_urls(testdata)
        self.assertEqual(result, expected_result)


class TestContentChecks(unittest.TestCase):

    @responses.activate
    def test_minimal(self):
        url = 'http://my.url'
        responses.add(responses.GET, url, status=200,
            content_type='text/html',
            body='<html></html>')
        r = requests.get(url)
        result = spider.check_content(r)

        del result['html']  # don't want to have the messy HTML part in comparison

        expected_result = {
            'icon': None,
            'title': None,
            'generator': None,
            'feeds': [],
            'encoding': 'iso-8859-1',
            'canonical_link': None,
            'opengraph': None
        }
        self.assertDictEqual(result, expected_result)

    @responses.activate
    def test_basic(self):
        url = 'http://my.url'
        responses.add(responses.GET, url, status=200,
            content_type='text/html; charset=UTF-8',
            body='''
                <!DOCTYPE html>
                <html>
                <head>
                    <title> The page's title </title>
                    <meta name="generator" content="some-cms/1.0">
                    <link rel="shortcut icon" href="http://foo.bar/image.png">
                    <link rel="alternate" type="application/rss+xml" href="http://example.com/feed">
                    <link rel="canonical" href="https://my.site.com/">
                </head>
                </html>
            ''')
        r = requests.get(url)
        result = spider.check_content(r)

        del result['html']  # don't want to have the messy HTML part in comparison

        expected_result = {
            'icon': 'http://foo.bar/image.png',
            'title': 'The page\'s title',
            'generator': 'some-cms/1.0',
            'feeds': [
                'http://example.com/feed',
            ],
            'encoding': 'utf-8',
            'canonical_link': 'https://my.site.com/',
            'opengraph': None
        }
        self.assertDictEqual(result, expected_result)

    @responses.activate
    def test_opengraph(self):
        url = 'http://my.url'
        responses.add(responses.GET, url, status=200,
            content_type='text/html; charset=UTF-8',
            body='''
                <html>
                <head>
                    <meta property="og:title" content="The Rock" />
                    <meta property="og:type" content="video.movie" />
                    <meta property="og:url" content="http://www.foor.bar" />
                    <meta property="og:image" content="http://www.foo.bar/foo.jpg" />
                </head>
                </html>
            ''')
        r = requests.get(url)
        result = spider.check_content(r)

        del result['html']  # don't want to have the messy HTML part in comparison

        expected_result = {
            'icon': None,
            'title': None,
            'generator': None,
            'feeds': [],
            'encoding': 'utf-8',
            'canonical_link': None,
            'opengraph': ['og:image', 'og:title', 'og:type', 'og:url'],
        }
        self.assertDictEqual(result, expected_result)


if __name__ == '__main__':
    unittest.main()
