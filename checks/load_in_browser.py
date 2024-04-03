"""
Collects information by loading pages in a browser.

Information includes:

- whether the document width adapts well to viewports as little as 360 pixels wide
- whether javascript errors or errors from missing resources occur
- what CSS font-family properties are in use
- what cookies are set during loading the page
"""

from datetime import datetime
import hashlib
import logging
import math
import os
import shutil
import time
import sqlite3
import json

from selenium import webdriver
from selenium.common.exceptions import StaleElementReferenceException
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By

import tenacity

from google.cloud import storage
from google.cloud import datastore

from checks.abstract_checker import AbstractChecker

class Checker(AbstractChecker):

    page_load_timeout = 120

    # sizes we check for (width, height)
    sizes = (
        (1920, 1080), # Full HD horizontal
        (1500, 1500), # useful window size we also use for the main screenshot
        (1024, 768), # older desktop or horiz. tablet
        (768, 1024), # older tablet or newer smartphone
        (360, 640), # rather old smartphone
    )

    def __init__(self, config, previous_results=None):
        super().__init__(config, previous_results)

        # Our selenium user agent using Chrome headless as an engine
        options = webdriver.ChromeOptions()
        options.add_argument('--enable-automation')
        options.add_argument('--headless=new')
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--dns-prefetch-disable')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-component-extensions-with-background-pages')
        options.add_argument('--disable-default-apps')
        options.add_argument('--hide-scrollbars')
        options.add_argument('--disk-cache-size=0')
        options.add_argument('--no-default-browser-check')
        options.add_argument('--no-first-run')
        options.add_argument('--ash-no-nudges')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-search-engine-choice-screen')
        options.add_argument('--verbose')
        options.page_load_strategy = 'normal'

        # path where to get cookies from
        options.add_argument("--user-data-dir=/opt/chrome-userdir")

        # empty /opt/chrome-userdir
        shutil.rmtree('/opt/chrome-userdir', ignore_errors=True)

        # Enable performance logging
        options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})

        self.driver = webdriver.Chrome(options=options)
        self.driver.set_page_load_timeout(self.page_load_timeout)

        # We capture the browser engine's user agent string
        # for the record.
        self.user_agent = self.driver.execute_script("return navigator.userAgent;")

    def run(self):
        """
        Main function of this check.
        """
        results = {}
        for url in self.config.urls:

            results[url] = {
                'cookies': None,
                'sizes': None,
                'min_document_width': None,
                'logs': None,
                'font_families': None,
                'performance_log': [],
                'screenshots': [],
            }

            self.driver.get(url)

            # Responsive layout check and screenshots.
            try:
                check_responsiveness_results = self.check_responsiveness(url)
                results[url] = {
                    'sizes': check_responsiveness_results['sizes'],
                    'min_document_width': min([s['document_width'] for s in check_responsiveness_results['sizes']]),
                    'dom_size': self.get_dom_size(),
                    'logs': self.capture_log(),
                    'performance_log': [],
                    'screenshots': check_responsiveness_results['screenshots'],
                }
            except TimeoutException as e:
                logging.warning("TimeoutException when checking responsiveness for %s: %s" % (url, e))
                pass
            except tenacity.RetryError as re:
                logging.warning("RetryError when checking responsiveness for %s: %s" % (url, re))
                pass
            
            # Scroll page to bottom, to load all lazy-loading resources.
            try:
                self.scroll_to_bottom()
            except TimeoutException as e:
                logging.warning("TimeoutException in scroll_to_bottom for %s: %s" % (url, e))
                pass
            except tenacity.RetryError as re:
                logging.warning("RetryError in scroll_to_bottom for %s: %s" % (url, re))
                pass

            # CSS collection
            font_families = None

            try:
                elements = self.driver.find_elements(By.XPATH, "//*")
                font_families = set()
                for element in elements:
                    try:
                        font_family = element.value_of_css_property('font-family')
                        if font_family is None:
                            continue
                        font_families.add(font_family.lower())
                    except StaleElementReferenceException as e:
                        logging.warning("StaleElementReferenceException when collecting CSS properties for %s: %s" % (url, e))
                        continue

                results[url]['font_families'] = sorted(list(font_families))
            
            except TimeoutException as e:
                logging.warning("TimeoutException when collecting CSS elements for %s: %s" % (url, e))
                pass
            
            # Process cookies.
            try:
                results[url]['cookies'] = self.get_cookies()
            except TimeoutException as e:
                logging.warning("TimeoutException when collecting cookies %s: %s" % (url, e))
                pass
            except tenacity.RetryError as re:
                logging.warning("RetryError when collecting cookies for %s: %s" % (url, re))
                pass
        
            for logentry in self.driver.get_log('performance'):
                decoded_logentry = json.loads(logentry['message'])
                results[url]['performance_log'].append(decoded_logentry)

        self.driver.quit()

        return results
    
    def post_hook(self, result):
        """
        Logic executed after run() is done.
        Used to upload screenshots and metadata to cloud storage and datastore.
        """
        # Upload screenshots and metadata

        logging.debug("load_in_browser post_hook 1 - Creating client")

        storage_client = storage.Client.from_service_account_json(self.config.storage_credentials_path)
        bucket = storage_client.get_bucket(self.config.screenshot_bucket_name)

        datastore_client = datastore.Client.from_service_account_json(self.config.datastore_credentials_path)
        exclude_from_indexes = ['size', 'screenshot_url', 'user_agent']

        for url in result.keys():
            for screenshot in result[url]['screenshots']:
                # Upload one screenshot
                try:
                    local_file = '%s/%s' % (screenshot['folder'], screenshot['filename'])

                    logging.debug("Handling screenshot file %s" % local_file)

                    if not os.path.exists(screenshot['local_path']):
                        logging.warning("No screenshot created: size=%s, url='%s'" % (screenshot['size'], screenshot['url']))
                        continue

                    logging.debug("Uploading %s to %s/%s" % (screenshot['local_path'], screenshot['folder'], screenshot['filename']))
                    with open(screenshot['local_path'], 'rb') as my_file:
                        # Create new blob in remote bucket
                        blob = bucket.blob(local_file)
                        blob.upload_from_file(my_file, content_type="image/png")
                        blob.make_public()
                except Exception as e:
                    logging.warning("Error uploading screenshot for %s: %s" % (screenshot['url'], e))
                    continue

                try:
                    os.remove(screenshot['local_path'])
                except:
                    pass
                
                # Write metadata for one screenshot
                data = {
                    'url': screenshot['url'],
                    'size': screenshot['size'],
                    'screenshot_url': screenshot['screenshot_url'],
                    'user_agent': screenshot['user_agent'],
                    'created': screenshot['created'],
                }
                try:
                    key = datastore_client.key(self.config.screenshot_datastore_kind, screenshot['screenshot_url'])
                    entity = datastore.Entity(key=key, exclude_from_indexes=exclude_from_indexes)
                    entity.update(data)
                    datastore_client.put(entity)
                    logging.debug("Successfully stored screenshot metadata for %s" % screenshot['screenshot_url'])
                except Exception as e:
                    logging.warning("Error in %s: %s" % (screenshot['url'], e))


            # Remove screenshots part from results
            del result[url]['screenshots']

        return result

    def get_cookies(self):
        # read cookie DB to get 3rd party cookies, too
        cookies = []
        db = sqlite3.connect('/opt/chrome-userdir/Default/Cookies')
        db.row_factory = sqlite3.Row
        c = db.cursor()
        c.execute("SELECT creation_utc, host_key, name, path, expires_utc, is_secure, is_httponly, has_expires, is_persistent FROM cookies")
        for row in c.fetchall():
            cookies.append(dict(row))
        c.close()
        db.close()
        
        return cookies

    @tenacity.retry(stop=tenacity.stop_after_attempt(3),
                    retry=tenacity.retry_if_exception_type(TimeoutException))
    def check_responsiveness(self, url):
        result = {
            'sizes': [],
            'screenshots': [],
        }

        # set window to the first size initially
        self.driver.set_window_size(self.sizes[0][0], self.sizes[0][1])

        for (width, height) in self.sizes:
            self.driver.set_window_size(width, height)
            
            # wait for re-render/re-flow
            time.sleep(1.0)
            doc_width = self.driver.execute_script("return document.body.scrollWidth")
            
            result['sizes'].append({
                'viewport_width': width,
                'document_width': int(doc_width),
            })

            # Make screenshot
            urlhash = hashlib.md5(bytearray(url, 'utf-8')).hexdigest()
            folder = "%sx%s" % (width, height)
            abs_folder = "/screenshots/%s" % folder
            os.makedirs(abs_folder, exist_ok=True)
            filename = urlhash + '.png'
            abs_filepath = "%s/%s" % (abs_folder, filename)
            created = datetime.utcnow()

            success = self.driver.save_screenshot(abs_filepath)

            if not success:
                logging.warning("Failed to create screenshot %s" % abs_filepath)
                continue

            result['screenshots'].append({
                'local_path': abs_filepath,
                'folder': folder,
                'filename': filename,
                'url': url,
                'size': [width, height],
                'screenshot_url': 'http://%s/%s/%s' % (
                    self.config.screenshot_bucket_name, folder, filename),
                'user_agent': self.user_agent,
                'created': created,
            })

        return result
    
    def get_dom_size(self):
        dom_length = self.driver.execute_script("return document.getElementsByTagName('*').length")
        return int(dom_length)
    
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
