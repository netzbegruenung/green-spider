import unittest

from spider.spider import check_and_rate_site

from pprint import pprint

class TestSpiderr(unittest.TestCase):

    def test_url1(self):

        entry = {
            "url": "https://httpbin.org/html",
            "type": "type",
            "state": "state",
            "level": "level",
            "district": "district",
            "city": "city",
        }

        url = "https://httpbin.org/html"
        result = check_and_rate_site(entry)

        self.assertEqual(result["input_url"], url)

if __name__ == '__main__':
    unittest.main()
