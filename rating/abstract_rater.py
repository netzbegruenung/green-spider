class AbstractRater(object):

    # String 'boolean' or 'number'
    rating_type = None

    # The default value to return if no rating given
    default_value = None
    
    max_score = 1

    # Name of the checks this rater depends on
    depends_on_checks = []

    def __init__(self, check_results):
        self.check_results = check_results

        for item in self.depends_on_checks:
            assert item in self.check_results

    def rate(self):
        raise NotImplementedError()
    
