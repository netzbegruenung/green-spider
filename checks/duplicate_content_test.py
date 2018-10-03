import httpretty
from httpretty import httprettified
import unittest

from checks import duplicate_content
from checks import page_content
from checks.config import Config

@httprettified
class TestDuplicateContent(unittest.TestCase):

    def test_similar(self):
        page_body = """
            <html>
                <head>
                    <title>Title</title>
                </head>
                <body>
                    <h1 class="title">Headline</h1>
                    <p class="intro">Second paragraph with <strong>strong words</strong></p>
                    <p class="text">Third paragraph</p>
                    <ul class="somelist">
                        <li>A list item</li>
                    </ul>
                </body>
            </html>
        """

        url1 = 'http://example.com/'
        httpretty.register_uri(httpretty.GET, url1, body=page_body)

        url2 = 'http://www.example.com/'
        httpretty.register_uri(httpretty.GET, url2, body=page_body)

        results = {}

        config = Config(urls=[url1, url2])
        page_content_checker = page_content.Checker(config=config, previous_results={})
        results['page_content'] = page_content_checker.run()

        checker = duplicate_content.Checker(config=page_content_checker.config,
                                            previous_results=results)
        result = checker.run()
        urls_after = checker.config.urls

        self.assertEqual(result, {
            'http://example.com/ http://www.example.com/': {
                'exception': None,
                'similarity': 1.0
            }
        })
        self.assertEqual(urls_after, ['http://example.com/'])


if __name__ == '__main__':
    unittest.main()
