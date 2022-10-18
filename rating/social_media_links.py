"""
Checks whether the pages have a link to social media profiles.
"""

from rating.abstract_rater import AbstractRater
from urllib.parse import urlparse
import logging

class Rater(AbstractRater):

    rating_type = 'boolean'
    default_value = False
    depends_on_checks = ['hyperlinks']
    max_score = 1

    def __init__(self, check_results):
        super().__init__(check_results)
    
    def rate(self):
        value = self.default_value
        score = 0

        urls = 0
        urls_with_social_media_links = 0

        for url in self.check_results['hyperlinks']:

            urls += 1

            for link in self.check_results['hyperlinks'][url]['links']:
                
                if link['href'] is None:
                    continue

                # only process absolute links
                if not (link['href'].startswith('http:') or link['href'].startswith('https:')):
                    continue
                
                parsed = urlparse(link['href'])
                if parsed is None:
                    continue
                if parsed.hostname is None:
                    continue

                if ("facebook.com" in parsed.hostname or
                    "twitter.com" in parsed.hostname or
                    "instagram.com" in parsed.hostname or
                    "gruene.social" in parsed.hostname):
                    logging.debug("Found social media link on %s: %s" % (url, link['href']))
                    urls_with_social_media_links += 1
                    
                    # make sure we only count 1 for this url
                    break

        if urls > 0 and urls_with_social_media_links == urls:
            score = self.max_score
            value = True

        return {
            'type': self.rating_type,
            'value': value,
            'score': score,
            'max_score': self.max_score,
        }
