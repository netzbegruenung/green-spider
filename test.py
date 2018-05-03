import unittest
import spider

class TestSpider(unittest.TestCase):

    def test_derive_test_hostnames1(self):
        hn = spider.derive_test_hostnames('www.my-domain.de')
        expected = ['my-domain.de', 'www.my-domain.de']
        self.assertEqual(hn, expected)

    def test_derive_test_hostnames2(self):
        hn = spider.derive_test_hostnames('domain.de')
        expected = ['domain.de', 'www.domain.de']
        self.assertEqual(hn, expected)

if __name__ == '__main__':
    unittest.main()
