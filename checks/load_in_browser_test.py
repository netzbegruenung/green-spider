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

        # A page that reflows to fit a 360px-wide viewport reports a document
        # width of exactly 360 (it fills the viewport without overflowing), so
        # "fits" means <= 360, not < 360.
        self.assertLessEqual(result[url]['min_document_width'], 360)
        self.assertEqual(result[url]['cookies'], [])
        # The missing favicon.ico is expected to produce a log entry. We don't
        # assert an exact total, as the CI runner's network can surface extra
        # transient resource warnings that aren't relevant to this check.
        favicon_logs = [entry for entry in result[url]['logs']
                        if 'favicon.ico' in entry['message']]
        self.assertEqual(len(favicon_logs), 1)
        self.assertEqual(result[url]['font_families'], ['"times new roman"'])

        viewport_widths = [s['viewport_width'] for s in result[url]['sizes']]
        self.assertIn(390, viewport_widths)  # emulated iPhone
        self.assertIn(360, viewport_widths)  # emulated Android (and legacy desktop 360x640)


if __name__ == '__main__':
    unittest.main()
