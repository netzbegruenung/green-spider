import httpretty
from httpretty import httprettified
import unittest

from checks import html_head, page_content
from checks import load_feeds
from checks.config import Config
from datetime import datetime

from pprint import pprint

@httprettified
class TestFeed(unittest.TestCase):

    def test_feed_rss2(self):
        """
        Checks RSS 2.0
        """

        feed = """<?xml version="1.0"?>
            <rss version="2.0">
                <channel>
                    <title>Liftoff News</title>
                    <link>http://liftoff.msfc.nasa.gov/</link>
                    <description>Liftoff to Space Exploration.</description>
                    <pubDate>Tue, 10 Jun 2003 04:00:00 GMT</pubDate>
                    <item>
                        <title>Star City</title>
                        <link>http://liftoff.msfc.nasa.gov/news/2003/news-starcity.asp</link>
                        <pubDate>Tue, 03 Jun 2003 09:39:21 GMT</pubDate>
                        <guid>http://liftoff.msfc.nasa.gov/2003/06/03.html#item573</guid>
                    </item>
                    <item>
                        <description>Sky watchers in Europe, Asia, and parts of Alaska and Canada will experience a &lt;a href="http://science.nasa.gov/headlines/y2003/30may_solareclipse.htm"&gt;partial eclipse of the Sun&lt;/a&gt; on Saturday, May 31st.</description>
                        <pubDate>Fri, 30 May 2003 11:06:42 GMT</pubDate>
                        <guid>http://liftoff.msfc.nasa.gov/2003/05/30.html#item572</guid>
                    </item>
                </channel>
            </rss>
        """

        feed_url = 'http://example.com/feed.xml'
        httpretty.register_uri(httpretty.GET, feed_url,
                               body=feed,
                               adding_headers={
                                   "Content-type": "application/rss+xml",
                               })

        # mocking a previous result from some page
        results = {
            'html_head': {
                'http://example.com/': {
                    'link_rss_atom': ['http://example.com/feed.xml']
                }
            }
        }
        config = Config(urls=['http://example.com/'])
        checker = load_feeds.Checker(config=config, previous_results=results)

        result = checker.run()
        pprint(result)

        self.assertEqual(result['http://example.com/feed.xml'], {
            'exception': None,
            'average_interval': 340359,
            'first_entry': datetime(2003, 5, 30, 11, 6, 42),
            'latest_entry': datetime(2003, 6, 3, 9, 39, 21),
            'num_entries': 2,
            'title': 'Liftoff News',
        })


    def test_empty_feed_rss2(self):
        """
        Checks RSS 2.0
        """

        feed = """<?xml version="1.0"?>
            <rss version="2.0">
                <channel>
                    <title>Empty Feed</title>
                    <link>http://example.com/</link>
                    <pubDate></pubDate>
                </channel>
            </rss>
        """

        feed_url = 'http://example.com/feed.xml'
        httpretty.register_uri(httpretty.GET, feed_url,
                               body=feed,
                               adding_headers={
                                   "Content-type": "application/rss+xml",
                               })

        # mocking a previous result from some page
        results = {
            'html_head': {
                'http://example.com/': {
                    'link_rss_atom': ['http://example.com/feed.xml']
                }
            }
        }
        config = Config(urls=['http://example.com/'])
        checker = load_feeds.Checker(config=config, previous_results=results)

        result = checker.run()
        pprint(result)

        self.assertEqual(result, {
            'http://example.com/feed.xml': {
                'exception': None,
                'title': 'Empty Feed',
                'latest_entry': None,
                'first_entry': None,
                'average_interval': None,
                'num_entries': 0,
            }
        })


    def test_feed_rss2_without_dates(self):
        """
        Checks RSS 2.0
        """

        feed = """<?xml version="1.0"?>
            <rss version="2.0">
                <channel>
                    <title>Liftoff News</title>
                    <link>http://liftoff.msfc.nasa.gov/</link>
                    <description>Liftoff to Space Exploration.</description>
                    <item>
                        <title>Star City</title>
                        <link>http://liftoff.msfc.nasa.gov/news/2003/news-starcity.asp</link>
                        <guid>http://liftoff.msfc.nasa.gov/2003/06/03.html#item573</guid>
                    </item>
                    <item>
                        <description>Sky watchers in Europe, Asia, and parts of Alaska and Canada will experience a &lt;a href="http://science.nasa.gov/headlines/y2003/30may_solareclipse.htm"&gt;partial eclipse of the Sun&lt;/a&gt; on Saturday, May 31st.</description>
                        <guid>http://liftoff.msfc.nasa.gov/2003/05/30.html#item572</guid>
                    </item>
                </channel>
            </rss>
        """

        feed_url = 'http://example.com/feed.xml'
        httpretty.register_uri(httpretty.GET, feed_url,
                               body=feed,
                               adding_headers={
                                   "Content-type": "application/rss+xml",
                               })

        # mocking a previous result from some page
        results = {
            'html_head': {
                'http://example.com/': {
                    'link_rss_atom': ['http://example.com/feed.xml']
                }
            }
        }
        config = Config(urls=['http://example.com/'])
        checker = load_feeds.Checker(config=config, previous_results=results)

        result = checker.run()
        pprint(result)

        self.assertEqual(result, {
            'http://example.com/feed.xml': {
                'exception': None,
                'title': 'Liftoff News',
                'latest_entry': None,
                'first_entry': None,
                'average_interval': None,
                'num_entries': 2,
            }
        })



if __name__ == '__main__':
    unittest.main()
