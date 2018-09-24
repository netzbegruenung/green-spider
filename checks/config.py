class Config(object):
    """
    Our configuration to be passed to checks
    """

    def __init__(self, urls):
        self._urls = set(urls)
    
    def __repr__(self):
      return "Config(urls=%r)" % self._urls

    @property
    def urls(self):
        return list(self._urls)

    def add_url(self, url):
        self._urls.add(url)
