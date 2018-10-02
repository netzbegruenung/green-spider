"""
If all URLs could be loaded without severe network errors, this rater gives a score.
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

        found_pageloads = 0
        found_errors = 0
        for url in self.check_results['load_in_browser']:
            if (self.check_results['load_in_browser'][url]['logs'] == [] or
                self.check_results['load_in_browser'][url]['logs'] is None):
                continue
            
            found_pageloads += 1
            
            # scan log entries for script errors
            for entry in self.check_results['load_in_browser'][url]['logs']:
                if entry['source'] != 'network':
                    continue
                if entry['level'] != 'SEVERE':
                    continue
                
                found_errors += 1

        if found_pageloads > 0 and found_errors == 0:
            value = True
            score = self.max_score

        return {
            'type': self.rating_type,
            'value': value,
            'score': score,
            'max_score': self.max_score,
        }
