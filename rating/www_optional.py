"""
This looks at reachable URLs and checks whether (sub)domains
both with and without www. are reachable.
"""

from urllib.parse import urlparse

from rating.abstract_rater import AbstractRater

class Rater(AbstractRater):

    rating_type = 'boolean'
    default_value = False
    depends_on_checks = ['url_reachability']
    max_score = 1

    def __init__(self, check_results):
        super().__init__(check_results)
    
    def rate(self):
        value = self.default_value
        score = 0

        hostnames = set()
        for url in self.check_results['url_reachability']:
            if self.check_results['url_reachability'][url]['exception'] is not None:
                continue
            parsed = urlparse(url)
            hostnames.add(parsed)
        
        # FIXME
        # we simply check whether there is more than one hostname.
        # this works with our current input URls but might be too
        # simplistic in the future.
        if len(list(hostnames)) > 1:
            value = True
            score = self.max_score

        return {
            'type': self.rating_type,
            'value': value,
            'score': score,
            'max_score': self.max_score,
        }
