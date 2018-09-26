"""
This check verifies whether the urls in config are reachable.
Some additional information regarding redirects and SSL problems
are also recorded and returned as results.

Non-accessible URLs are removed from config.urls.

TODO: Parallelize the work done in this test
"""

import logging

import requests

from checks.abstract_checker import AbstractChecker


class Checker(AbstractChecker):
    def __init__(self, config, previous_results=None):
        super().__init__(config, previous_results)
    
    def run(self):
        headers = {
            "User-Agent": self.config.user_agent
        }

        results = {}
        urls = list(self.config.urls)

        for url in urls:
            logging.debug("Checking URL reachability for %s", url)

            result = {
                "url": url,
                "redirect_history": None,
                "status": None,
                "exception": None,
                "duration": None,
            }
            
            # Perform HEAD requests, recording redirect log
            try:
                r = requests.head(url, headers=headers, allow_redirects=True)
                result['status'] = r.status_code
                result['duration'] = round(r.elapsed.total_seconds() * 1000)

                if len(r.history):
                    result['redirect_history'] = self.expand_history(r.history)
                    logging.debug("Redirects: %r", result['redirect_history'])

                if r.url == url:
                    logging.debug("URL: %s - status %s", url, r.status_code)
                else:
                    logging.debug("URL: %s - status %s - redirects to %s", url,
                        r.status_code, r.url)
                    # remove source URL, add target URL to config.urls
                    self.config.remove_url(url)
                    self.config.add_url(r.url)

            except Exception as exc:
                logging.info("Exception for URL %s: %s %s", url, str(type(exc)), exc)
                result['exception'] = {
                    'type': str(type(exc)),
                    'message': str(exc),
                }
                
                # remove URL to prevent further checks on unreachable URL
                self.config.remove_url(url)

            results[url] = result
        
        return results

    def expand_history(self, history):
        """Extracts primitives from a list of requests.Response objects"""
        items = []
        for h in history:
            item = {
                'status': h.status_code,
                'duration': round(h.elapsed.total_seconds() * 1000),
                'redirect_to': h.headers['location'],
            }
            items.append(item)
        
        return items
