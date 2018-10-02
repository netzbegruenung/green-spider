"""
Checks whether the pages use the font 'Arvo'.
"""

from rating.abstract_rater import AbstractRater

class Rater(AbstractRater):

    rating_type = 'boolean'
    default_value = False
    depends_on_checks = ['load_in_browser']
    max_score = 1

    def __init__(self, check_results):
        super().__init__(check_results)
    
    def rate(self):
        value = self.default_value
        score = 0

        urls_with_font = 0
        urls_without_font = 0
        for url in self.check_results['load_in_browser']:
            if self.check_results['load_in_browser'][url]['font_families'] is None:
                urls_without_font += 1
                continue
            
            fonts = " ".join(self.check_results['load_in_browser'][url]['font_families'])
            if 'arvo' in fonts:
                urls_with_font += 1
        
        if urls_with_font > 0 and urls_without_font == 0:
            score = self.max_score
            value = True

        return {
            'type': self.rating_type,
            'value': value,
            'score': score,
            'max_score': self.max_score,
        }
