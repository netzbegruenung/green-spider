"""
This gives a score if one of the input URL's hostnames was resolvable
"""

from rating.abstract_rater import AbstractRater

class Rater(AbstractRater):

    rating_type = 'boolean'
    default_value = False
    depends_on_checks = ['dns_resolution']
    max_score = 1

    def __init__(self, check_results):
        super().__init__(check_results)
    
    def rate(self):
        value = self.default_value
        score = 0

        count = 0
        for url in self.check_results['dns_resolution']:
            if self.check_results['dns_resolution'][url]['resolvable_ipv4']:
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
