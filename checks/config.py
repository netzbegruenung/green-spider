class Config(object):
    """
    Our configuration to be passed to checks
    """

    def __init__(self,
                 urls,
                 screenshot_bucket_name,
                 screenshot_datastore_kind,
                 storage_credentials_path,
                 datastore_credentials_path,
                 user_agent='green-spider/1.0'):
        self._urls = set(urls)
        self._user_agent = user_agent
        self._screenshot_bucket_name = screenshot_bucket_name
        self._screenshot_datastore_kind = screenshot_datastore_kind
        self._storage_credentials_path = storage_credentials_path
        self._datastore_credentials_path = datastore_credentials_path
    
    def __repr__(self):
      return "Config(urls=%r)" % self._urls

    @property
    def urls(self):
        return sorted(list(self._urls))

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
    
    @property
    def screenshot_bucket_name(self):
        return self._screenshot_bucket_name
    
    @property
    def storage_credentials_path(self):
        return self._storage_credentials_path

    @property
    def datastore_credentials_path(self):
        return self._datastore_credentials_path
    
    @property
    def screenshot_datastore_kind(self):
        return self._screenshot_datastore_kind
