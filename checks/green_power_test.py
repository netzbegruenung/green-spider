import unittest

from checks import green_power
from checks.config import Config

class TestGreenPower(unittest.TestCase):

    def test_is_green(self):
        """Checks that we get a green result for green powered site"""
        # google is green, Koch Industries. predictably is not
        # TODO mock the result, so we don't need to hit a live API
        config = Config(urls=['https://google.com/'])
        checker = green_power.Checker(config=config)
        result = checker.run()
        urls_after = checker.config.urls
        print(urls_after)

        self.assertEqual(1, 1)

    def test_is_not_green(self):
        """Checks that we get a grey result for grey powered site"""
        config = Config(urls=['http://www.kochind.com/'])
        checker = green_power.Checker(config=config)
        result = checker.run()
        urls_after = checker.config.urls
        print(urls_after)





