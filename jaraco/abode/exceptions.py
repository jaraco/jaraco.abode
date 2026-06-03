import builtins
from http import HTTPStatus

import requests

#: HTTP status codes Abode uses to signal an authentication/authorization failure.
AUTH_STATUS_CODES = frozenset({
    HTTPStatus.BAD_REQUEST,
    HTTPStatus.UNAUTHORIZED,
    HTTPStatus.FORBIDDEN,
})

#: Abode application-level error codes that are returned (sometimes with an
#: HTTP 200) when the stored authentication is expired or otherwise invalid.
AUTH_ERROR_CODES = frozenset({11002, 13027})

_AUTH_MESSAGE_MARKERS = ('unauthorized', 'invalid credentials')


def _looks_like_auth_message(message):
    """Return True if a free-form message string indicates an auth failure."""
    message = str(message or '').lower()
    return any(marker in message for marker in _AUTH_MESSAGE_MARKERS) or (
        'password' in message and 'match' in message
    )


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

    @classmethod
    def detect(cls, response):
        """Return True if ``response`` indicates an authentication failure.

        Abode signals authentication problems both through HTTP status codes
        (400/401/403) and, in some cases, through an error payload returned
        alongside an HTTP 200. Detecting the latter lets callers trigger
        reauthentication instead of treating the bogus payload as a success.
        """
        if response.status_code in AUTH_STATUS_CODES:
            return True
        if response.status_code != HTTPStatus.OK:
            return False
        return cls._auth_error_in_payload(response)

    @classmethod
    def from_response(cls, response):
        """Build an :class:`AuthenticationException` from ``response``."""
        return cls((response.status_code, cls.best_message(response)))

    @classmethod
    def _auth_error_in_payload(cls, response):
        # Check the content type first rather than blindly parsing the body.
        content_type = response.headers.get('Content-Type', '')
        if 'application/json' not in content_type.lower():
            return False
        try:
            payload = response.json()
        except ValueError:
            return False
        if not isinstance(payload, dict):
            return False
        return payload.get('errorCode') in AUTH_ERROR_CODES or _looks_like_auth_message(
            payload.get('message')
        )

    @staticmethod
    def best_message(response):
        content_type = response.headers.get('Content-Type', '')
        if 'application/json' in content_type.lower():
            try:
                payload = response.json()
            except ValueError:
                return response.text
            if isinstance(payload, dict) and 'message' in payload:
                return payload['message']
        return response.text


class SocketIOException(Exception):
    """Class to throw SocketIO Error exception."""

    def __init__(self, error, details):
        super().__init__(error)
        self.details = details
