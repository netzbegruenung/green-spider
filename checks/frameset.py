"""
Collects information on usage of the frameset tag
"""

import logging

from bs4 import BeautifulSoup

from checks.abstract_checker import AbstractChecker

class Checker(AbstractChecker):
    def __init__(self, config, previous_results=None):
        super().__init__(config, previous_results)

    def depends_on_results(self):
        return ['page_content']

    def run(self):
        assert 'page_content' in self.previous_results
        
        results = {}

        for url in self.config.urls:
            results[url] = self.get_framesets(url)

        return results
    
    def get_framesets(self, url):
        """
        Expects page_content_dict['content'] to carry the HTML content
        """
        page_content = self.previous_results['page_content'][url]
        assert 'content' in page_content

        if page_content['content'] is None:
            return

        result = {
            'frameset': None,
        }

        soup = BeautifulSoup(page_content['content'], 'html.parser')

        count = 0
        for _ in soup.find_all("frameset"):
            count += 1

        if count > 0:
            result['frameset'] = True
        else:
            result['frameset'] = False

        return result
