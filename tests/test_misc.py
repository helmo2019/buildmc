from unittest import TestCase

from buildmc.util import log, log_warn, log_error

class LoggingTests(TestCase):

    @staticmethod
    def test_logging():
        log('This is an informative message')
        log('Something happened, but the application may continue running', log_warn)
        log('A critical error occurred!', log_error)
