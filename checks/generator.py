"""
Checks the 'generator' meta tag and page content properties
to detect well-known content management systems, themes etc.
"""

import logging

from checks.abstract_checker import AbstractChecker

class Checker(AbstractChecker):

    # IP address of the newthinking GCMS server
    gcms_ip = "91.102.13.20"

    def __init__(self, config, previous_results=None):
        super().__init__(config, previous_results)
    
    def run(self):
        assert 'page_content' in self.previous_results
        assert 'html_head' in self.previous_results
        assert 'dns_resolution' in self.previous_results

        results = {}

        for url in self.config.urls:
            results[url] = self.get_generator(url)

        return results


    def get_generator(self, url):
        page_content = self.previous_results['page_content'][url]
        assert 'content' in page_content

        dns_resolution = self.previous_results['dns_resolution']

        head = self.previous_results['html_head'][url]

        generator = None

        if 'generator' in head and head['generator'] is not None:
            generator = head['generator'].lower()
            if 'typo3' in generator:
                generator = 'typo3'
            if 'wordpress' in generator:
                generator = 'wordpress'
            if 'drupal' in generator:
                generator = 'drupal'
            if 'joomla' in generator:
                generator = 'joomla'
            if 'drupal' in generator:
                generator = 'drupal'
        
        # Qualify certain CMS flavours in more detail
        if generator == "typo3":
            # Typo3-Gruene advertises in the page content
            if 'typo3-gruene.de' in page_content['content']:
                generator = "typo3-gruene"
            # newthinking GCMS in some page hrefs
            elif 'ntc_gcms' in page_content['content']:
                generator = "typo3-gcms"
            # check if one of the IPs matches the well-known GCMS Server IP
            elif url in dns_resolution:
                for addr in dns_resolution[url]['ipv4_addresses']:
                    if addr == self.gcms_ip:
                        generator = "typo3-gcms"

        elif 'Urwahl3000' in page_content['content']:
            generator = "wordpress-urwahl"

        elif ('josephknowsbest' in page_content['content'] or
            'Joseph-knows-best' in page_content['content']):
            generator = "wordpress-josephknowsbest"

        elif 'wordpress' in page_content['content']:
            generator = "wordpress"
        
        return generator
