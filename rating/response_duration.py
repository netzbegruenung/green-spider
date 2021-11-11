"""
This looks at the response duration(s) and scores based on the bucket
the value is in. Fast responses get one point, slower half a point,
more than a seconds gets nothing.
"""

from rating.abstract_rater import AbstractRater

class Rater(AbstractRater):

    rating_type = 'number'
    default_value = 0
    depends_on_checks = ['page_content']
    max_score = 1.0

    def __init__(self, check_results):
        super().__init__(check_results)
    
    def rate(self):
        value = self.default_value
        score = 0

        duration_sum = 0
        duration_count = 0

        for url in self.check_results['page_content']:
            if self.check_results['page_content'][url]['exception'] is not None:
                continue
            duration_sum += self.check_results['page_content'][url]['duration']
            duration_count += 1
        
        if duration_count > 0:
            value = round(duration_sum / duration_count)
        
            # value is duration in milliseconds
            if value < 100:
                score = self.max_score
            elif value < 1000:
                score = self.max_score * 0.5

        return {
            'type': self.rating_type,
            'value': value,
            'score': score,
            'max_score': self.max_score,
        }
