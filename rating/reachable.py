"""
This gives a score if one of the checked URL variations was reachable.
"""

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

        count = 0
        for url in self.check_results['url_reachability']:
            if self.check_results['url_reachability'][url]['exception'] is not None:
                continue
            count += 1
        
        if count > 0:
            value = True
            score = self.max_score

        return {
            'type': self.rating_type,
            'value': value,
            'score': score,
            'max_score': self.max_score,
        }
