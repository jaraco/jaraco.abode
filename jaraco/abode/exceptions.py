import requests


class AbodeException(Exception):
    """Class to throw general abode exception."""

    def __init__(self, error, details=None):
        """Initialize AbodeException."""
        # Call the base class constructor with the parameters it needs
        super().__init__(error[1])

        self.errcode = error[0]
        self.message = error[1]
        self.details = details


class AbodeAuthenticationException(AbodeException):
    """Class to throw authentication exception."""

    @classmethod
    def raise_for(cls, response):
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as exc:
            raise cls((response.status_code, cls.best_message(response))) from exc

    @staticmethod
    def best_message(response):
        if response.headers.get('Content-Type') == 'application/json':
            return response.json()['message']
        return response.text


class SocketIOException(AbodeException):
    """Class to throw SocketIO Error exception."""
