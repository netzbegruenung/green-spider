"""
This looks at all HTTPS URLs we checked for reachability.

If all of them were reachable without errors, we give full score.
If some or all had errors, or no HTTPS URL is reachable, we give zero.
"""

from rating.abstract_rater import AbstractRater

class Rater(AbstractRater):

    rating_type = 'boolean'
    default_value = False
    depends_on_checks = ['url_reachability']

    # HTTPS is very important, so this counts double
    max_score = 2

    def __init__(self, check_results):
        super().__init__(check_results)
    
    def rate(self):
        value = self.default_value
        score = 0

        reachable_count = 0
        unreachable_count = 0

        for url in self.check_results['url_reachability']:
            if not url.startswith('https://'):
                continue

            if self.check_results['url_reachability'][url]['exception'] is None:
                reachable_count += 1
            else:
                unreachable_count += 1
        
        if unreachable_count == 0 and reachable_count > 0:
            value = True
            score = self.max_score

        return {
            'type': self.rating_type,
            'value': value,
            'score': score,
            'max_score': self.max_score,
        }
