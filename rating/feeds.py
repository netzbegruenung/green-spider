"""
This gives a score if the site has feeds.
"""

from rating.abstract_rater import AbstractRater

class Rater(AbstractRater):

    rating_type = 'boolean'
    default_value = False
    depends_on_checks = ['html_head']
    max_score = 1

    def __init__(self, check_results):
        super().__init__(check_results)
    
    def rate(self):
        value = self.default_value
        score = 0

        for url in self.check_results['html_head']:
            if self.check_results['html_head'][url]['link_rss_atom'] is None:
                continue
            if self.check_results['html_head'][url]['link_rss_atom'] == []:
                continue
            value = True
            score = self.max_score
            break

        return {
            'type': self.rating_type,
            'value': value,
            'score': score,
            'max_score': self.max_score,
        }
