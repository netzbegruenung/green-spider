"""
This checks the result for an url using green power, and returns
a boolean based on whether it's using green power or not
"""

from rating.abstract_rater import AbstractRater

class Rater(AbstractRater):

    rating_type = 'boolean'
    default_value = False
    depends_on_checks = ['green_power']
    max_score = 1

    def __init__(self, check_results):
        super().__init__(check_results)

    def rate(self):
        value = self.default_value
        score = 0

        if check_results['green_power']:
            value = True
            score = self.max_score

        return {
            'type': self.rating_type,
            'value': value,
            'score': score,
            'max_score': self.max_score,
        }