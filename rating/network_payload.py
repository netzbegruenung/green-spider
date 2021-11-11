"""
This rater evaluates the amount of data transferred for a page load.

Currently no score is given. The plan is however to reward site that
cause smaller transfers.

The rater uses Chrome performance log messages of type
'Network.loadingFinished'.
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

        payloads_for_urls = []

        for url in self.check_results['load_in_browser']:
            payload = 0

            if (self.check_results['load_in_browser'][url]['performance_log'] == [] or
                self.check_results['load_in_browser'][url]['performance_log'] is None):
                continue
            
            for lentry in self.check_results['load_in_browser'][url]['performance_log']:
                if lentry['message']['method'] == 'Network.loadingFinished':
                    payload += lentry['message']['params']['encodedDataLength']
            
            payloads_for_urls.append(payload)
        
        # Calculate score based on the largest value found for a URL.
        # See https://github.com/netzbegruenung/green-spider/issues/11#issuecomment-600307544
        # for details.
        if len(payloads_for_urls) > 0:
            value = max(payloads_for_urls)
            if value < 994000:
                score = 1
            elif value < 1496000:
                score = .5

        return {
            'type': self.rating_type,
            'value': value,
            'score': score,
            'max_score': self.max_score,
        }
