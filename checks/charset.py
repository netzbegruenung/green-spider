"""
Checks which character set a page has.

TODO: Check for http-equiv meta tags like
      <meta http-equiv="content-type" content="text/html; charset=iso-8859-1" />
"""

import logging

from bs4 import BeautifulSoup

from checks.abstract_checker import AbstractChecker

class Checker(AbstractChecker):
    def __init__(self, config, previous_results=None):
        super().__init__(config, previous_results)
    
    def run(self):
        results = {}

        for url in self.config.urls:
            results[url] = self.get_charset(url)

        return results
    
    def get_charset(self, url):
        """
        Expects page_content_dict['content'] to carry the HTML content
        """

        page_content = self.previous_results['page_content'][url]
        assert 'content' in page_content
        assert 'response_headers' in page_content
        logging.debug("%r", page_content['response_headers'])
        assert 'content-type' in page_content['response_headers']

        if page_content['content'] is None:
            return

        result = {
            'meta_charset_tag': None,
            'content_type_header_charset': None,
            'charset': 'iso-8859-1', # ISO-8859-1 is the default according to https://www.w3.org/International/articles/http-charset/index
            'valid': None,
            'exception': None,
        }

        soup = BeautifulSoup(page_content['content'], 'html.parser')

        # get response header charset
        if ('content-type' in page_content['response_headers']
            and 'charset=' in page_content['response_headers']['content-type']):
            parts = page_content['response_headers']['content-type'].split("charset=", 1)
            result['content_type_header_charset'] = parts[1].lower()
            result['charset'] = parts[1].lower()

        # get meta tag charset
        metatags = soup.find_all('meta')
        for tag in metatags:
            if 'charset' in tag.attrs:
                result['meta_charset_tag'] = tag['charset'].lower()
                # meta tag overrules any previous value
                result['charset'] = tag['charset'].lower()
        
        # check for charset plausibility (only for most common ones)
        if result['charset'] in ('iso-8859-1', 'utf-8'):
            try:
                _ = page_content['content'].encode(result['charset'])
            except UnicodeEncodeError as e:
                result['valid'] = False
                result['exception'] = str(e)
            else:
                result['valid'] = True


        return result
