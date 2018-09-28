"""
This looks at remaining resolvable URLs after redirects
and gives score if there is only one URL left.
"""

from rating.abstract_rater import AbstractRater

class Rater(AbstractRater):

    rating_type = 'boolean'
    default_value = False
    depends_on_checks = ['url_canonicalization']
    max_score = 1

    def __init__(self, check_results):
        super().__init__(check_results)
    
    def rate(self):
        value = self.default_value
        score = 0

        if len(self.check_results['url_reachability']) == 1:
            value = True
            score = self.max_score

        return {
            'type': self.rating_type,
            'value': value,
            'score': score,
            'max_score': self.max_score,
        }
