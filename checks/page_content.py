"""
This check downloads the HTML page for each URL
"""

import logging

import requests

from checks.abstract_checker import AbstractChecker


class Checker(AbstractChecker):

    # connection timeout (seconds)
    CONNECT_TIMEOUT = 10

    # response timeout (seconds)
    READ_TIMEOUT = 20

    def __init__(self, config, previous_results=None):
        super().__init__(config, previous_results)


    def run(self):
        results = {}

        self.headers = {
            "User-Agent": self.config.user_agent,
        }

        # copy URLs, as we may be manipulating self.config.urls in the loop
        url = list(self.config.urls)

        for url in self.config.urls:
            result = self.download_page(url)
            results[url] = result

            # remove bad URLs from config, to avoid later checks using them
            if 'exception' in result and result['exception'] is not None:
                self.config.remove_url(url)
        
        return results


    def download_page(self, url):
        result = {
            'url': url,
            'content': None,
            'content_type': None,
            'content_length': None,
            'status_code': None,
            'response_headers': None,
            'duration': None,
            'exception': None,
        }

        try:
            r = requests.get(url,
                             headers=self.headers,
                             timeout=(self.CONNECT_TIMEOUT, self.READ_TIMEOUT))
            
            result['url'] = r.url
            result['status_code'] = r.status_code
            result['content'] = r.text
            result['content_length'] = len(r.text)
            result['response_headers'] = self.get_headers(r.headers)
            result['duration'] = round(r.elapsed.total_seconds() * 1000)

            if r.headers.get("content-type") is not None:
                result['content_type'] = r.headers.get("content-type").split(";")[0].strip()

        except requests.exceptions.ConnectionError as exc:
            logging.error(str(exc) + " " + url)
            result['exception'] = "connection"
        except requests.exceptions.ReadTimeout as exc:
            logging.error(str(exc) + " " + url)
            result['exception'] = "read_timeout"
        except requests.exceptions.Timeout as exc:
            logging.error(str(exc) + " " + url)
            result['exception'] = "connection_timeout"
        except Exception as exc:
            logging.error(str(exc) + " " + url)
            result['exception'] = "%s %s" % (str(type(exc)), exc)
        
        return result
    
    def get_headers(self, headers):
        """
        Transforms CaseInsensitiveDict into dict with lowercase keys
        """
        out = {}
        for key in headers:
            out[key.lower()] = headers[key]
        return out
