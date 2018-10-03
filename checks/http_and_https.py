"""
This adds, for every HTTP URL, the HTTPS counterpart,
and vice versa, to config.urls

So it doesn't actually perform tests. It only expands the
URLs to test by other checks.
"""

from checks.abstract_checker import AbstractChecker

class Checker(AbstractChecker):
    def __init__(self, config, previous_results=None):
        super().__init__(config, previous_results)
    
    def run(self):
        """
        Adds URLs to config.urls, returns nothing
        """

        for url in self.config.urls:
            
            if url.startswith('https://'):
                self.config.add_url('http://' + url[8:])
            elif url.startswith('http://'):
                self.config.add_url('https://' + url[7:])

        return None