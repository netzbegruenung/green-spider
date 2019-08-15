"""
Collects information on mobile friendliness by loading pages
in an emulated mobile browser.
"""

import logging
import math
import time
import os
from multiprocessing import Pool

import requests

from checks.abstract_checker import AbstractChecker

class Checker(AbstractChecker):

    def __init__(self, config, previous_results=None):
        super().__init__(config, previous_results)

    def run(self):
        # Create multiprocessing pool with 4 slots.
        pool = Pool(4)
        results = {}

        for url in self.config.urls:

            # responsive check
            try:
                results[url] = pool.apply_async(self.check_mobile_friendliness, (url,))
            except Exception as e:
                logging.warn("Exception caught when checking mobile friendliness for %s: %s" % (url, e))
                pass
            
        pool.close()
        pool.join()

        results_final = {}
        for url in results.keys():
            results_final[url] = results[url].get()

        return results_final

    def check_mobile_friendliness(self, url):
        api_key = os.environ.get("GOOGLE_URL_TESTING_API_KEY")
        api_url = "https://searchconsole.googleapis.com/v1/urlTestingTools/mobileFriendlyTest:run?key=%s" % api_key
        params = {"url": url}
        
        r = requests.post(api_url, json=params, timeout=30)
        r.raise_for_status()

        if r.status_code == 200:
            return r.json()
        return None