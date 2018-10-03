import httpretty
from httpretty import httprettified
import unittest

from checks import charset
from checks import page_content
from checks.config import Config

@httprettified
class TestCharsetChecker(unittest.TestCase):

    def test_http_response(self):
        url = 'http://www.example.com/'
        httpretty.register_uri(httpretty.GET, url,
            body="""<html>
                <head>
                <meta http-equiv="Content-type" value="text/html; charset=foo">
                <meta charset="utf-8">
                <title>Hello</title>
                </head>
            </html>""",
            adding_headers={
                "Content-Type": "text/html; charset=ISO-8859-1",
            })
        
        results = {}

        config = Config(urls=[url])
        page_content_checker = page_content.Checker(config=config, previous_results={})
        results['page_content'] = page_content_checker.run()

        self.assertIn(url, results['page_content'])
        self.assertIn('response_headers', results['page_content'][url])
        self.assertIn('content-type', results['page_content'][url]['response_headers'])

        charset_checker = charset.Checker(config=page_content_checker.config, previous_results=results)
        result = charset_checker.run()

        self.assertIn(url, result)
        self.assertEqual(result[url], {
            'meta_charset_tag': 'utf-8',
            'content_type_header_charset': 'iso-8859-1',
            'charset': 'utf-8',
            'valid': True,
            'exception': None,
        })

if __name__ == '__main__':
    unittest.main()
