import httpretty
from httpretty import httprettified
import unittest

from checks import hyperlinks
from checks import page_content
from checks.config import Config

@httprettified
class TestHyperlinks(unittest.TestCase):

    def test_links(self):
        self.maxDiff = 2000
        page_body = """
            <html>
                <head>
                    <title>Title</title>
                </head>
                <body>
                    <a href="/">Home</a>
                    <a href="/sub/">Sub page</a>
                    <a href="/"> Spaces </a>
                    <a href="https://www.google.com/">External</a>
                    <a href="/" style="display: hidden">Hidden</a>
                    <a href="/" style="display: none">Hidden</a>
                </body>
            </html>
        """

        url = 'http://example.com/'
        httpretty.register_uri(httpretty.GET, url, body=page_body)

        results = {}

        config = Config(urls=[url])
        page_content_checker = page_content.Checker(config=config, previous_results={})
        results['page_content'] = page_content_checker.run()

        checker = hyperlinks.Checker(config=page_content_checker.config,
                                            previous_results=results)
        result = checker.run()
        urls_after = checker.config.urls

        self.assertEqual(result, {
            'http://example.com/': {
                'links': [
                    {'href': '/', 'text': 'Home'},
                    {'href': '/sub/', 'text': 'Sub page'},
                    {'href': '/', 'text': 'Spaces'},
                    {'href': 'https://www.google.com/', 'text': 'External'},
                    {'href': '/', 'text': 'Hidden'},
                    {'href': '/', 'text': 'Hidden'},
                ],
                'exception': None,
            }
        })
        self.assertEqual(urls_after, ['http://example.com/'])


if __name__ == '__main__':
    unittest.main()
