class AbstractChecker(object):
    """
    Our blueprint for checks
    """

    def __init__(self, config, previous_results=None):
        self._config = config

        # A dictionary of results from previous checkers.
        # Key is the name of the checker that has generated the result.
        self._previous_results = previous_results

    def run(self):
        """Executes the check routine, returns result dict"""
        raise NotImplementedError()

    @property
    def config(self):
        return self._config
    
    @property
    def previous_results(self):
        return self._previous_results
