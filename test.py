import unittest
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


if __name__ == '__main__':
    unittest.main()
