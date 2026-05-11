import httpretty
from httpretty import httprettified
import unittest

from checks import duplicate_content
from checks import page_content
from checks.config import Config


class TestSimilarity(unittest.TestCase):

    def test_identical_documents(self):
        html = "<html><body><h1 class='a b'>x</h1><p class='c'>y</p></body></html>"
        self.assertEqual(duplicate_content._similarity(html, html), 1.0)

    def test_identical_structure_different_classes(self):
        html1 = "<html><body><h1 class='a'>x</h1><p class='b'>y</p></body></html>"
        html2 = "<html><body><h1 class='c'>x</h1><p class='d'>y</p></body></html>"
        self.assertEqual(duplicate_content._structural_similarity(html1, html2), 1.0)
        self.assertEqual(duplicate_content._style_similarity(html1, html2), 0.0)
        self.assertEqual(duplicate_content._similarity(html1, html2), 0.5)

    def test_identical_classes_different_structure(self):
        html1 = "<html><body><h1 class='a'>x</h1></body></html>"
        html2 = "<html><body><div class='a'><span class='a'>x</span></div></body></html>"
        self.assertEqual(duplicate_content._style_similarity(html1, html2), 1.0)
        self.assertLess(duplicate_content._structural_similarity(html1, html2), 1.0)

    def test_completely_different(self):
        html1 = "<html><body><h1 class='a'>x</h1></body></html>"
        html2 = "<html><body><div class='b'><span class='c'>y</span><p class='d'>z</p></div></body></html>"
        self.assertLess(duplicate_content._similarity(html1, html2), 0.7)

    def test_k_parameter_weights(self):
        # structural=1.0, style=0.0 → similarity == k
        html1 = "<html><body><h1 class='a'>x</h1><p class='b'>y</p></body></html>"
        html2 = "<html><body><h1 class='c'>x</h1><p class='d'>y</p></body></html>"
        self.assertAlmostEqual(duplicate_content._similarity(html1, html2, k=0.0), 0.0)
        self.assertAlmostEqual(duplicate_content._similarity(html1, html2, k=1.0), 1.0)
        self.assertAlmostEqual(duplicate_content._similarity(html1, html2, k=0.25), 0.25)

    def test_multiple_classes_per_element_are_split(self):
        html = "<html><body><div class='foo bar baz'>x</div></body></html>"
        self.assertEqual(duplicate_content._get_classes(html), {'foo', 'bar', 'baz'})

    def test_no_classes_returns_empty_set(self):
        html = "<html><body><div>x</div></body></html>"
        self.assertEqual(duplicate_content._get_classes(html), set())

    def test_style_similarity_both_empty_is_one(self):
        # Jaccard of two empty sets is defined as 1.0 (both pages share "no classes")
        html1 = "<html><body><h1>x</h1></body></html>"
        html2 = "<html><body><p>y</p></body></html>"
        self.assertEqual(duplicate_content._style_similarity(html1, html2), 1.0)

    def test_jaccard_similarity_disjoint(self):
        self.assertEqual(duplicate_content._jaccard_similarity({'a'}, {'b'}), 0.0)

    def test_jaccard_similarity_partial_overlap(self):
        self.assertAlmostEqual(
            duplicate_content._jaccard_similarity({'a', 'b'}, {'b', 'c'}), 1 / 3)

    def test_jaccard_similarity_both_empty(self):
        self.assertEqual(duplicate_content._jaccard_similarity(set(), set()), 1.0)

    def test_jaccard_similarity_one_empty(self):
        self.assertEqual(duplicate_content._jaccard_similarity({'a'}, set()), 0.0)

    def test_html_comments_are_handled(self):
        # Comments should be counted as a 'comment' tag, not raise
        html1 = "<html><body><!-- a comment --><p>x</p></body></html>"
        html2 = "<html><body><!-- a comment --><p>x</p></body></html>"
        self.assertEqual(duplicate_content._structural_similarity(html1, html2), 1.0)


@httprettified
class TestDuplicateContent(unittest.TestCase):

    def test_identical(self):
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
