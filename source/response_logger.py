"""
Logger utility for logging request responses only once.
"""

import requests
import threading

from Log import *


class ResponseLogger:
    """
    Logger for request responses that only logs the first time for a given HTTP
    status code.
    """

    def __init__(self):
        """ Initializes the logger. """
        self.logged = {}
        self.lock = threading.Lock()

    def log_if_first(self, base_key: str, response: requests.Response):
        """
        Purpose:
            Logs the details of the given response if a previous response for the same
            status code has not already been logged.
        Args:
            base_key: Key to differentiate different requests
            response: Request response
        """
        with self.lock:
            key = f"{base_key}:{response.status_code}"
            if key not in self.logged:
                self.logged[key] = True
                logError(
                    (
                        f"Response for {response.request.method} {response.url}: "
                        f"Status Code: {response.status_code} ({response.reason}) "
                        f"Headers: {response.headers} "
                        f"Content: {response.content}"
                    )
                )
