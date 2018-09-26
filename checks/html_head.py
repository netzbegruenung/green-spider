"""
Extracts information from the html <head>, like existence and value
of certain meta tags, link tags, title, etc.
"""

import logging
import re
from urllib.parse import urljoin
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from checks.abstract_checker import AbstractChecker

class Checker(AbstractChecker):
    def __init__(self, config, previous_results=None):
        super().__init__(config, previous_results)
    
    def run(self):
        results = {}

        for url in self.config.urls:
            results[url] = self.get_content(url)

        return results
    
    def get_content(self, url):
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

        soup = BeautifulSoup(page_content['content'], 'html.parser')
        head = soup.find('head')

        result = {
            'title': self.get_title(head),
            'link_canonical': self.get_link_canonical(head, url),
            'link_rss_atom': self.get_link_rss_atom(head, url),
            'link_icon': self.get_link_icon(head, url),
            'generator': self.get_generator(head),
            'get_opengraph': self.get_opengraph(head),
        }

        return result


    def get_title(self, head):
        """Extract and clean up page title"""
        if head is None:
            return
        
        title = None

        tag = head.find('title')
        if tag is None:
            return
        
        title = tag.get_text()
        
        # clean up
        title = title.replace(u'\u00a0', ' ')
        title = title.replace('  ', ' ')
        title = title.strip()

        return title
        

    def get_link_canonical(self, head, url):
        if head is None:
            return
        link = head.find('link', rel='canonical')
        if link:
            return urljoin(url, link.get('href'))
    

    def get_link_rss_atom(self, head, url):
        if head is None:
            return
        hrefs = []
        rss_links = head.find_all('link', type='application/rss+xml')
        atom_links = head.find_all('link', type='application/atom+xml')

        if rss_links:
            for link in rss_links:
                hrefs.append(link.get('href'))
        if atom_links:
            for link in rss_links:
                hrefs.append(link.get('href'))
        
        # make URLs absolute
        for i in range(len(hrefs)):
            parsed = urlparse(hrefs[i])
            if parsed.scheme == '':
                hrefs[i] = urljoin(url, hrefs[i])

        return hrefs

    
    def get_link_icon(self, head, url):
        if head is None:
            return

        tag = head.find('link', rel=lambda x: x and x.lower() == 'icon')
        if tag:
            return urljoin(url, tag.get('href'))
        tag = head.find('link', rel=lambda x: x and x.lower() == 'shortcut icon')
        if tag:
            return urljoin(url, tag.get('href'))


    def get_generator(self, head):
        if head is None:
            return

        tags = head.select('[name=generator]')
        if tags:
            return tags[0].get('content')


    def get_opengraph(self, head):
        if head is None:
            return

        # we find tags by matching this property/itemprop value regex
        property_re = re.compile('^og:')

        opengraph = set()
        for tag in head.find_all(property=property_re):
            opengraph.add(tag.get('property'))
        for tag in head.find_all(itemprop=property_re):
            opengraph.add(tag.get('itemprop'))
        
        opengraph = sorted(list(opengraph))
        if opengraph != []:
            return opengraph
