"""
Collects information by loading pages in a browser.

Information includes:

- whether the document width adapts well to viewports as little as 360 pixels wide
- whether javascript errors or errors from missing resources occur
- collects CSS font-family properties in use
"""

import logging
import time

from selenium import webdriver
from selenium.common.exceptions import StaleElementReferenceException
from selenium.common.exceptions import TimeoutException
import tenacity

from checks.abstract_checker import AbstractChecker


class Checker(AbstractChecker):

    page_load_timeout = 20

    # sizes we check for (width, height)
    sizes = (
        (360, 640), # rather old smartphone
        (768, 1024), # older tablet or newer smartphone
        (1024, 768), # older desktop or horiz. tablet
        (1920, 1080), # Full HD horizontal
    )

    def __init__(self, config, previous_results=None):
        super().__init__(config, previous_results)

        # Our selenium user agent using Chrome headless as an engine
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-extensions')
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.set_page_load_timeout(self.page_load_timeout)

    def run(self):

        results = {}
        for url in self.config.urls:

            results[url] = {
                'sizes': None,
                'min_document_width': None,
                'logs': None,
                'font_families': None,
            }

            # responsive check
            try:
                sizes = self.check_responsiveness(url)
                results[url] = {
                    'sizes': sizes,
                    'min_document_width': min([s['document_width'] for s in sizes]),
                    'logs': self.capture_log(),
                }
            except TimeoutException as e:
                logging.warn("TimeoutException when checking responsiveness for %s: %s" % (url, e))
                pass
            except tenacity.RetryError as re:
                logging.warn("RetryError when checking responsiveness for %s: %s" % (url, re))
                pass
            
            # CSS collection
            font_families = None

            try:
                elements = self.driver.find_elements_by_xpath("//*")
                font_families = set()
                for element in elements:
                    try:
                        font_family = element.value_of_css_property('font-family')
                        if font_family is None:
                            continue
                        font_families.add(font_family.lower())
                    except StaleElementReferenceException as e:
                        logging.warn("StaleElementReferenceException when collecting CSS properties for %s: %s" % (url, e))
                        continue

                results[url]['font_families'] = sorted(list(font_families))
            
            except TimeoutException as e:
                logging.warn("TimeoutException when collecting CSS elements for %s: %s" % (url, e))
                pass

        self.driver.quit()

        return results


    @tenacity.retry(stop=tenacity.stop_after_attempt(3),
                    retry=tenacity.retry_if_exception_type(TimeoutException))
    def check_responsiveness(self, url):
        result = []

        # set window to the first size initially
        self.driver.set_window_size(self.sizes[0][0], self.sizes[0][1])
        self.driver.get(url)

        # give the page some time to load
        time.sleep(10)

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
    
    def capture_log(self):
        """
        Returns log elements with level "SEVERE"
        """
        entries = []
        for entry in self.driver.get_log('browser'):
            if entry['level'] in ('WARNING', 'SEVERE'):
                entries.append(entry)
        return entries
