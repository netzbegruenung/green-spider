"""
Loads feeds linked from pages and collects information on the contained content
"""

import logging
from time import mktime
from datetime import datetime

import feedparser

from checks.abstract_checker import AbstractChecker

class Checker(AbstractChecker):
    def __init__(self, config, previous_results=None):
        super().__init__(config, previous_results)
        self.feeds = {}

    def depends_on_results(self):
        return ['html_head']

    def run(self):
        assert 'html_head' in self.previous_results

        for url in self.config.urls:
            self.collect_feeds(url)

        for feed_url in self.feeds:
            self.feeds[feed_url] = self.analyse_feed(feed_url)

        return self.feeds
    
    def collect_feeds(self, url):
        """
        This collects the feeds from all urls.
        The assumption is that in most cases the urls will reference the same
        feeds.
        """
        head = self.previous_results['html_head'][url]
        if 'link_rss_atom' not in head:
            return
        if not isinstance(head['link_rss_atom'], list):
            return
        
        for feed_url in head['link_rss_atom']:
            if feed_url not in self.feeds:
                self.feeds[feed_url] = {}

        result = {
            'feeds': [],
            'exception': None,
        }

        return result
    

    def analyse_feed(self, feed_url):
        result = {
            'exception': None,
            'title': None,
            'latest_entry': None,
            'first_entry': None,
            'average_interval': None,
            'num_entries': None,
        }

        logging.debug("Loading feed %s" % feed_url)
        data = feedparser.parse(feed_url)

        if 'bozo_exception' in data:
            result['exception'] = str(data['bozo_exception'])

        if 'headers' not in data:
            return result

        if data['headers'].get('status') not in ('200', '301', '302'):
            result['exception'] = 'Server responded with status %s' % data['headers'].get('status')
        
        if 'feed' in data:
            result['title'] = data['feed'].get('title')
        if 'entries' in data:
            result['num_entries'] = len(data['entries'])
            result['latest_entry'] = self.find_latest_entry(data['entries'])
            result['first_entry'] = self.find_first_entry(data['entries'])
            if (result['num_entries'] > 1 and 
                result['first_entry'] is not None and
                result['latest_entry'] is not None and
                result['first_entry'] < result['latest_entry']):
                result['average_interval'] = round((result['latest_entry'] - result['first_entry']).total_seconds() / (result['num_entries'] - 1))
        
        return result


    def find_latest_entry(self, entries):
        max_date = None

        for entry in entries:
            published_parsed = entry.get('published_parsed')
            if published_parsed is None:
                return
            timestamp = mktime(published_parsed)
            if max_date is None or timestamp > max_date:
                max_date = timestamp
        
        if max_date is not None:
            return datetime.fromtimestamp(max_date)


    def find_first_entry(self, entries):
        min_date = None

        for entry in entries:
            published_parsed = entry.get('published_parsed')
            if published_parsed is None:
                return
            timestamp = mktime(published_parsed)
            if min_date is None or timestamp < min_date:
                min_date = timestamp
        
        if min_date is not None:
            return datetime.fromtimestamp(min_date)
