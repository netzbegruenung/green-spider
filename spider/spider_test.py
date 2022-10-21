import unittest
from pprint import pprint

from spider.spider import check_and_rate_site

class TestSpider(unittest.TestCase):

    """
    Simply calls the spider.check_and_rate_site function
    with httpbin.org URLs. We don't assert a lot here,
    but at least make sure that most of our code is executed
    in tests.
    """

    def test_html(self):
        """Loads a simple HTML web page"""

        entry = {
            "url": "https://httpbin.org/html",
            "type": "type",
            "state": "state",
            "level": "level",
            "district": "district",
            "city": "city",
        }

        url = "https://httpbin.org/html"
        try:
            result = check_and_rate_site(entry)
            self.assertEqual(result["input_url"], url)
        except ValueError:
            pass

if __name__ == '__main__':
    unittest.main()
