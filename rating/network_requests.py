"""
This rater evaluates the number of network requests made.

Currently no score is given. The plan is however to reward site that
use only few requests.

The rater uses Chrome performance log messages of type
'Network.requestWillBeSent'.
"""

from rating.abstract_rater import AbstractRater

class Rater(AbstractRater):

    rating_type = 'number'
    default_value = 0
    depends_on_checks = ['load_in_browser']
    max_score = 1.0

    def __init__(self, check_results):
        super().__init__(check_results)
    
    def rate(self):
        value = self.default_value
        score = 0

        num_requests_for_urls = []

        for url in self.check_results['load_in_browser']:
            num_requests = 0

            if (self.check_results['load_in_browser'][url]['performance_log'] == [] or
                self.check_results['load_in_browser'][url]['performance_log'] is None):
                continue
            
            for lentry in self.check_results['load_in_browser'][url]['performance_log']:
                if lentry['message']['method'] == 'Network.requestWillBeSent':
                    num_requests += 1
            
            num_requests_for_urls.append(num_requests)
        
        # Calculate score based on the largest value found for a URL.
        # See https://github.com/netzbegruenung/green-spider/issues/11#issuecomment-600307544
        # for details.
        if len(num_requests_for_urls) > 0:
            value = max(num_requests_for_urls)
            if value <= 28:
                score = 1.0
            elif value <= 38:
                score = 0.5

        return {
            'type': self.rating_type,
            'value': value,
            'score': score,
            'max_score': self.max_score,
        }
