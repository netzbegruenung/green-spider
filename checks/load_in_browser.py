"""
Collects information by loading pages in a browser.

Information includes:

- whether the document width adapts well to viewports as little as 360 pixels wide
- whether javascript errors or errors from missing resources occur
- what CSS font-family properties are in use
- what cookies are set during loading the page
"""

import logging
import math
import shutil
import time
import sqlite3

from selenium import webdriver
from selenium.common.exceptions import StaleElementReferenceException
from selenium.common.exceptions import TimeoutException
import tenacity

from checks.abstract_checker import AbstractChecker

class Checker(AbstractChecker):

    page_load_timeout = 30

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

        # path where to get cookies from
        chrome_options.add_argument("--user-data-dir=/opt/chrome-userdir")

        # empty /opt/chrome-userdir
        shutil.rmtree('/opt/chrome-userdir', ignore_errors=True)

        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.set_page_load_timeout(self.page_load_timeout)

    def run(self):

        results = {}
        for url in self.config.urls:

            results[url] = {
                'cookies': None,
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
            
            try:
                self.scroll_to_bottom()
            except TimeoutException as e:
                logging.warn("TimeoutException in scroll_to_bottom for %s: %s" % (url, e))
                pass
            except tenacity.RetryError as re:
                logging.warn("RetryError in scroll_to_bottom for %s: %s" % (url, re))
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
            
            try:
                results[url]['cookies'] = self.get_cookies()
            except TimeoutException as e:
                logging.warn("TimeoutException when collecting cookies %s: %s" % (url, e))
                pass
            except tenacity.RetryError as re:
                logging.warn("RetryError when collecting cookies for %s: %s" % (url, re))
                pass

        self.driver.quit()

        return results

    def get_cookies(self):
        # read cookie DB to get 3rd party cookies, too
        cookies = []
        db = sqlite3.connect('/opt/chrome-userdir/Default/Cookies')
        db.row_factory = sqlite3.Row
        c = db.cursor()
        c.execute("SELECT creation_utc, host_key, name, path, expires_utc, is_secure, is_httponly, has_expires, is_persistent, firstpartyonly FROM cookies")
        for row in c.fetchall():
            cookies.append(dict(row))
        c.close()
        db.close()
        
        return cookies

    @tenacity.retry(stop=tenacity.stop_after_attempt(3),
                    retry=tenacity.retry_if_exception_type(TimeoutException))
    def check_responsiveness(self, url):
        result = []

        # set window to the first size initially
        self.driver.set_window_size(self.sizes[0][0], self.sizes[0][1])
        self.driver.get(url)

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
        Returns log elements with level "SEVERE" or "WARNING"
        """
        entries = []
        for entry in self.driver.get_log('browser'):
            if entry['level'] in ('WARNING', 'SEVERE'):
                entries.append(entry)
        return entries
    
    @tenacity.retry(stop=tenacity.stop_after_attempt(3),
                    retry=tenacity.retry_if_exception_type(TimeoutException))
    def scroll_to_bottom(self):
        """
        Scroll through the entire page once to trigger loading of all resources
        """
        height = self.driver.execute_script("return document.body.scrollHeight")
        height = int(height)
        pages = math.floor(height / 1000)
        for _ in range(0, pages):
            self.driver.execute_script("window.scrollBy(0,1000)")
            time.sleep(0.2)
