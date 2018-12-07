import httpretty
from httpretty import httprettified
import unittest

from checks import frameset
from checks import page_content
from checks.config import Config

@httprettified
class TestFrameset(unittest.TestCase):

    def test_frameset_positive(self):
        page_body = """
            <!doctype html public "-//w3c//dtd html 4.0 transitional//en">
            <html>
                <head>
                    <title>A frameset page</title>
                </head>
                <frameset framespacing="0" border="false" frameborder="0" rows="30,*">
                    <frame name="top" src="top.htm" scrolling="no">
                    <frame name="base" src="titel.htm" target="_top">
                    <noframes>
                        <body>
                            <p>Here we have some body content</p>
                        </body>
                    </noframes>
                </frameset>
            </html>
        """

        url = 'http://example.com/'
        httpretty.register_uri(httpretty.GET, url, body=page_body)

        results = {}

        config = Config(urls=[url])
        page_content_checker = page_content.Checker(config=config, previous_results={})
        results['page_content'] = page_content_checker.run()

        checker = frameset.Checker(config=page_content_checker.config,
                                   previous_results=results)
        result = checker.run()
        urls_after = checker.config.urls

        self.assertEqual(result, {
            'http://example.com/': {'frameset': True}
        })
        self.assertEqual(urls_after, ['http://example.com/'])


    def test_frameset_negative(self):
        page_body = """
            <!doctype html public "-//w3c//dtd html 4.0 transitional//en">
            <html>
                <head>
                    <title>A frameset page</title>
                </head>
                <body>
                    <p>Here we have some body content</p>
                </body>
            </html>
        """

        url = 'http://example.com/'
        httpretty.register_uri(httpretty.GET, url, body=page_body)

        results = {}

        config = Config(urls=[url])
        page_content_checker = page_content.Checker(config=config, previous_results={})
        results['page_content'] = page_content_checker.run()

        checker = frameset.Checker(config=page_content_checker.config,
                                   previous_results=results)
        result = checker.run()
        urls_after = checker.config.urls

        self.assertEqual(result, {
            'http://example.com/': {'frameset': False}
        })
        self.assertEqual(urls_after, ['http://example.com/'])


if __name__ == '__main__':
    unittest.main()
