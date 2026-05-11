import unittest
from pprint import pprint

from checks import load_in_browser
from checks.config import Config

class TestLoadInBrowser(unittest.TestCase):

    def test_basics(self):
        """Loads a simple HTML web page to check basic functionality"""
        url = 'https://httpbin.org/html'
        config = Config(urls=[url])
        checker = load_in_browser.Checker(config=config, previous_results={})
        result = checker.run()

        self.assertIn(url, result)
        self.assertIn('cookies', result[url])
        self.assertIn('font_families', result[url])
        self.assertIn('logs', result[url])
        self.assertIn('min_document_width', result[url])
        self.assertIn('sizes', result[url])

        self.assertTrue(result[url]['min_document_width'] < 360)
        self.assertEqual(result[url]['cookies'], [])
        self.assertEqual(len(result[url]['logs']), 1) # one log entry regarding favicon.ico is expected
        self.assertEqual(result[url]['font_families'], ['"times new roman"'])

        viewport_widths = [s['viewport_width'] for s in result[url]['sizes']]
        self.assertIn(390, viewport_widths)  # emulated iPhone
        self.assertIn(360, viewport_widths)  # emulated Android (and legacy desktop 360x640)


if __name__ == '__main__':
    unittest.main()
