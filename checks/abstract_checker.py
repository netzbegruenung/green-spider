class AbstractChecker(object):
    """
    Our blueprint for checks
    """

    def __init__(self, config):
        self._config = config

    def run(self):
        """Executes the check routine, returns result dict"""
        raise NotImplementedError()

    @property
    def config(self):
        return self._config