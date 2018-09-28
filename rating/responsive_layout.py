"""
This gives a score if the site's minimal document width during checks
was smaller than or equal to the minimal viewport size tested.
"""

from rating.abstract_rater import AbstractRater

class Rater(AbstractRater):

    rating_type = 'boolean'
    default_value = False
    depends_on_checks = ['responsive_layout']
    max_score = 1

    def __init__(self, check_results):
        super().__init__(check_results)
    
    def rate(self):
        value = self.default_value
        score = 0

        for url in self.check_results['responsive_layout']:
            if (self.check_results['responsive_layout'][url]['min_document_width'] <=
                self.check_results['responsive_layout'][url]['sizes'][0]['viewport_width']):
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
