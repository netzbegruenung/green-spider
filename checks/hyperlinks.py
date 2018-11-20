"""
Collects information on hyperlinks on the page.
"""

import logging

from bs4 import BeautifulSoup

from checks.abstract_checker import AbstractChecker

class Checker(AbstractChecker):
    def __init__(self, config, previous_results=None):
        super().__init__(config, previous_results)
    
    def run(self):
        assert 'page_content' in self.previous_results
        
        results = {}

        for url in self.config.urls:
            results[url] = self.get_links(url)

        return results
    
    def get_links(self, url):
        """
        Expects page_content_dict['content'] to carry the HTML content
        """
        page_content = self.previous_results['page_content'][url]
        assert 'content' in page_content

        if page_content['content'] is None:
            return

        result = {
            'links': [],
            'exception': None,
        }

        soup = BeautifulSoup(page_content['content'], 'html.parser')

        for link in soup.find_all("a"):
            result['links'].append({
                'href': link.get('href'),
                'text': link.text.strip(),
            })

        return result
