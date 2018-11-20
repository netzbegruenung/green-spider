"""
Checks whether the pages has a link "Kontakt"
"""

from rating.abstract_rater import AbstractRater

class Rater(AbstractRater):

    rating_type = 'boolean'
    default_value = False
    depends_on_checks = ['hyperlinks']
    max_score = 1

    def __init__(self, check_results):
        super().__init__(check_results)
    
    def rate(self):
        value = self.default_value
        score = 0

        urls = 0
        urls_with_contact_link = 0

        for url in self.check_results['hyperlinks']:

            urls += 1

            for link in self.check_results['hyperlinks'][url]['links']:
                if link['text'].lower() == 'kontakt':
                    urls_with_contact_link += 1

        if urls_with_contact_link == urls:
            score = self.max_score
            value = True

        return {
            'type': self.rating_type,
            'value': value,
            'score': score,
            'max_score': self.max_score,
        }
