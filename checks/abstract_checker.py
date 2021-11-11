class AbstractChecker(object):
    """
    Our blueprint for checks
    """

    def __init__(self, config, previous_results=None):
        self._config = config

        # A dictionary of results from previous checkers.
        # Key is the name of the checker that has generated the result.
        self._previous_results = previous_results

    def depends_on_results(self):
        """
        Should return  the name(s) of checks this one depends on.
        Empty list means this check has no prerequisites.
        """
        return []

    def run(self):
        """Executes the check routine, returns result dict"""
        raise NotImplementedError()
    
    def post_hook(self, result):
        """
        Optional function to execute after run(). Can be used to post-process
        results data. Should be defined by the implementing checker.

        Params:
          result: Result data from the run() function.
        
        Returns:
          Dict: Modified results data
          None: Means that nothing has been done, so should be ignored.
        """
        return None
    
    @property
    def config(self):
        return self._config
    
    @property
    def previous_results(self):
        return self._previous_results
