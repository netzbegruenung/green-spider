"""
Adds a point if the site sets no third party cookies.
"""

import logging
from urllib.parse import urlparse

from rating.abstract_rater import AbstractRater

class Rater(AbstractRater):

    rating_type = 'boolean'
    default_value = False
    depends_on_checks = ['load_in_browser']
    max_score = 1

    def __init__(self, check_results):
        super().__init__(check_results)
    
    def rate(self):
        value = self.default_value
        score = 0

        found_urls = 0
        found_urls_with_third_party_cookie = 0

        for url in self.check_results['load_in_browser']:
            found_urls += 1

            if (self.check_results['load_in_browser'][url]['cookies'] == [] or 
                self.check_results['load_in_browser'][url]['cookies'] is None):
                # no cookies for this URL
                continue
            
            # scan cookies for URL match
            if type(self.check_results['load_in_browser'][url]['cookies']) is list:
                parsed = urlparse(url)

                for cookie in self.check_results['load_in_browser'][url]['cookies']:
                    if parsed.netloc.endswith(cookie['host_key']):
                        # first party cookie
                        logging.debug("Cookie with host_key %s matches site URL %s" % (cookie['host_key'], parsed.netloc))
                        continue

                    # third party cookie
                    logging.debug("Cookie with host_key %s is a third party cookie" % cookie['host_key'])
                    found_urls_with_third_party_cookie += 1
                    break

        if found_urls > 0 and found_urls_with_third_party_cookie == 0:
            value = True
            score = self.max_score

        return {
            'type': self.rating_type,
            'value': value,
            'score': score,
            'max_score': self.max_score,
        }
