"""
Check for responsive layout.

This relies on 
"""

import logging
import time

from selenium import webdriver

from checks.abstract_checker import AbstractChecker


class Checker(AbstractChecker):

    page_load_timeout = 20

    # sizes we check for (width, height)
    sizes = (
        (320, 480), # old smartphone
        (360, 640), # slightly newer smartphone
        (768, 1024), # older tablet or newer smartphone
        (1024, 768), # older desktop or horiz. tablet
        (1920, 1080), # Full HD horizontal
    )

    def __init__(self, config, previous_results=None):
        super().__init__(config, previous_results)

    def run(self):
        # Our selenium user agent using Chrome headless as an engine
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-extensions')
        self.driver = webdriver.Chrome(chrome_options=chrome_options)
        self.driver.set_page_load_timeout(self.page_load_timeout)

        results = {}
        for url in self.config.urls:
            results[url] = self.check_responsiveness(url)
        return results


    def check_responsiveness(self, url):
        result = []

        # set window to the first size initially
        self.driver.set_window_size(self.sizes[0][0], self.sizes[0][1])
        self.driver.get(url)

        # give the page some time to load
        time.sleep(2)

        for (width, height) in self.sizes:
            self.driver.set_window_size(width, height)
            
            # wait for re-render/re-flow
            time.sleep(1.0)
            doc_width = self.driver.execute_script("return document.body.scrollWidth")
            
            result.append({
                'viewport_width': width,
                'document_width': int(doc_width),
            })

        return result