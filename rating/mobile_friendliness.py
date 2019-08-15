"""
This gives a score if the site is considered as mobile friendly.
"""

from rating.abstract_rater import AbstractRater

class Rater(AbstractRater):

    rating_type = 'boolean'
    default_value = False
    depends_on_checks = ['mobile_friendliness']
    max_score = 1

    def __init__(self, check_results):
        super().__init__(check_results)
    
    def rate(self):
        value = self.default_value
        score = 0

        for url in self.check_results['mobile_friendliness']:

            if 'mobileFriendliness' not in self.check_results['mobile_friendliness'][url]:
                continue

            if self.check_results['mobile_friendliness'][url]['mobileFriendliness'] == "MOBILE_FRIENDLY":
                value = True
                score = self.max_score
                # we use the first URL found here
                break

        return {
            'type': self.rating_type,
            'value': value,
            'score': score,
            'max_score': self.max_score,
        }
