"""
This checker looks at the similarity between previously downloaded pages
and removes duplicates from the config URLs
"""

import logging

import html_similarity

from checks.abstract_checker import AbstractChecker


class Checker(AbstractChecker):

    # value above which we consider a page pair a duplicate
    similarity_threshold = 0.99999

    def __init__(self, config, previous_results=None):
        super().__init__(config, previous_results)


    def run(self):

        if len(self.config.urls) == 1:
            # nothing to do for us
            return
        
        urls = list(self.config.urls)

        # get content
        content = {}

        assert 'page_content' in self.previous_results

        for url in urls:
            page_content = self.previous_results['page_content'][url]

            if page_content['content'] is None:
                logging.warning("Content for URL %s is None" % url)

            content[url] = page_content['content']
        
        pairs = self.compare_pairwise(content)

        # remove duplicates
        for key in pairs:
            if pairs[key]['similarity'] is None:
                continue
            if pairs[key]['similarity'] > self.similarity_threshold:
                # this pair is a duplicate.
                # Decide which one to keep
                url1, url2 = key.split(" ", 1)
                reject = self.select_url_to_reject(url1, url2)
                self.config.remove_url(reject)

        return pairs


    def compare_pairwise(self, content):
        # compair pairwise
        pairs = {}

        for url1 in content:
            for url2 in content:
                
                if url1 == url2:
                    continue
                
                # avoid checking pairs twice
                pair_key = " ".join(sorted([url1, url2]))
                if pair_key in pairs:
                    continue

                try:
                    s = html_similarity.similarity(content[url1], content[url2])
                    logging.debug("Comparing pages for URLs %s and %s: similarity=%s", url1, url2, s)
                    pairs[pair_key] = {
                        'similarity': s,
                        'exception': None,
                    }
                except (AttributeError, ValueError) as e:
                    logging.error("html_similarity.similarity thre exception for URL pair %s and %s: %s", url1, url2, e)
                    pairs[pair_key] = {
                        'similarity': None,
                        'exception': str(e),
                    }
        
        return pairs


    def select_url_to_reject(self, url1, url2):
        """Determine which of two URLs to keep, which to reject"""

        # HTTPS takes precedence
        if url1.startswith('https://') and not url2.startswith('https://'):
            return url2
        elif url2.startswith('https://') and not url1.startswith('https://'):
            return url1
        
        # Shorter URL wins
        if len(url1) < len(url2):
            return url2
        elif len(url1) > len(url2):
            return url1
        
        # default behaviour
        return url1
