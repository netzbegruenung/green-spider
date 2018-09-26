class Config(object):
    """
    Our configuration to be passed to checks
    """

    def __init__(self, urls, user_agent):
        self._urls = set(urls)
        self._user_agent = user_agent
    
    def __repr__(self):
      return "Config(urls=%r)" % self._urls

    @property
    def urls(self):
        return list(self._urls)

    def add_url(self, url):
        self._urls.add(url)

    def remove_url(self, url):
        """Removes url from urls, if it was in there. Ignores errors."""
        try:
            self._urls.remove(url)
        except KeyError:
            pass
    
    @property
    def user_agent(self):
        return self._user_agent
