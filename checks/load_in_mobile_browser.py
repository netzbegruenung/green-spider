"""
Collects information on mobile friendliness by loading pages
in an emulated mobile browser.
"""

import logging
import math
import shutil
import time
import sqlite3

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import StaleElementReferenceException
from selenium.common.exceptions import TimeoutException
import tenacity

from checks.abstract_checker import AbstractChecker

class Checker(AbstractChecker):

    page_load_timeout = 30

    # See https://github.com/ChromeDevTools/devtools-frontend/blob/bd62b4d646a85a6b2f0860d3884c42fb5adc76d5/front_end/emulated_devices/module.json#L283
    # for details about the Nexus 5. It's a 360 x 640 pixel device with device-pixel-ratio of 3.
    mobile_emulation = {"deviceName": "Nexus 5"}

    def __init__(self, config, previous_results=None):
        super().__init__(config, previous_results)

        # Our selenium user agent using Chrome headless as an engine
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_experimental_option("mobileEmulation", self.mobile_emulation)

        # empty /opt/chrome-userdir
        shutil.rmtree('/opt/chrome-userdir', ignore_errors=True)

        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.set_page_load_timeout(self.page_load_timeout)

    def run(self):

        results = {}
        for url in self.config.urls:

            results[url] = {
                'sizes': None,
                'min_document_width': None,
            }

            # responsive check
            try:
                result = self.check_responsiveness(url)
                results[url] = result
            except TimeoutException as e:
                logging.warn("TimeoutException when checking responsiveness for %s: %s" % (url, e))
                pass
            except tenacity.RetryError as re:
                logging.warn("RetryError when checking responsiveness for %s: %s" % (url, re))
                pass
        
        self.driver.quit()

        return results

    @tenacity.retry(stop=tenacity.stop_after_attempt(3),
                    retry=tenacity.retry_if_exception_type(TimeoutException))
    def check_responsiveness(self, url):
        self.driver.get(url)
        time.sleep(1.0)
        body_scroll_width = self.driver.execute_script("return document.body.scrollWidth")
        body_client_width = self.driver.execute_script("return document.body.clientWidth")
        window_inner_width = self.driver.execute_script("return window.innerWidth")
        window_outer_width = self.driver.execute_script("return window.outerWidth")
        screen_width = self.driver.execute_script("return screen.width")
        device_pixel_ratio = self.driver.execute_script("return window.devicePixelRatio")

        return {
            "body_scroll_width": int(body_scroll_width),
            "body_client_width": int(body_client_width),
            "window_inner_width": int(window_inner_width),
            "window_outer_width": int(window_outer_width),
            "device_pixel_ratio": int(device_pixel_ratio),
            "screen_width": int(screen_width),
        }
