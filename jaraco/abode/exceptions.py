import builtins
import requests


class Exception(builtins.Exception):
    """Class to throw general abode exception."""

    def __init__(self, error):
        super().__init__(*error)

    @property
    def errcode(self):
        code, _ = self.args
        return code

    @property
    def message(self):
        _, message = self.args
        return message


class AuthenticationException(Exception):
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


class SocketIOException(Exception):
    """Class to throw SocketIO Error exception."""
