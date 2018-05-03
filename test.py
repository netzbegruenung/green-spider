import unittest
import requests
import responses
import spider

class TestSpider(unittest.TestCase):

    def test_derive_test_hostnames(self):
        # case 1
        hn = spider.derive_test_hostnames('www.my-domain.de')
        expected = ['my-domain.de', 'www.my-domain.de']
        self.assertEqual(hn, expected)
        # case 2
        hn = spider.derive_test_hostnames('domain.de')
        expected = ['domain.de', 'www.domain.de']
        self.assertEqual(hn, expected)

    def test_reduce_urls(self):
        # This is our testdata
        testdata = [
            {'url': 'one', 'error': None, 'redirects_to': None},
            {'url': 'two', 'error': 'Yes', 'redirects_to': None},
            {'url': 'three', 'error': None, 'redirects_to': 'five'},
        ]
        expected_result = ['five', 'one']
        result = spider.reduce_urls(testdata)
        self.assertEqual(result, expected_result)

    @responses.activate
    def test_check_content1(self):
        """
        Very basic test of our content analysis function
        """
        url = 'http://my.url'
        responses.add(responses.GET, url, status=200,
            content_type='text/html',
            body='''
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="UTF-8">
                    <title>The title</title>
                </head>
                </html>
            ''')
        r = requests.get(url)
        result = spider.check_content(r)

        del result['html']  # don't want to have the messy HTML part in comparison

        expected_result = {
            'icon': None,
            'title': 'The title',
            'generator': None,
            'feeds': [],
            'encoding': 'ISO-8859-1',
            'canonical_link': None,
            'opengraph': None
        }
        self.assertDictEqual(result, expected_result)


if __name__ == '__main__':
    unittest.main()
