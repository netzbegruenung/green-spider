"""
This check verifies whether there is a single URL
or several variants left at this point.
"""

from checks.abstract_checker import AbstractChecker

class Checker(AbstractChecker):
    def __init__(self, config, previous_results=None):
        super().__init__(config, previous_results)
    
    def run(self):
        return self.config.urls
