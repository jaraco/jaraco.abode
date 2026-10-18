"""
Tests for runtime authentication-failure handling in ``Client.send_request``.

These cover the dedicated ``AuthenticationException`` that is raised when a
request fails because authentication is no longer valid, including the case
where Abode returns an auth-error payload alongside an HTTP 200 status.
"""

from http import HTTPStatus

import pytest

import jaraco.abode
from jaraco.abode.exceptions import AuthenticationException
from jaraco.abode.helpers import urls

from . import mock as MOCK
from .mock import devices as DEVICES
from .mock import login as LOGIN
from .mock import oauth_claims as OAUTH_CLAIMS
from .mock import panel as PANEL


class _FakeResponse:
    """Minimal stand-in for ``requests.Response`` for unit-testing helpers."""

    def __init__(self, status_code, *, content_type='application/json', payload=None):
        self.status_code = status_code
        self.headers = {'Content-Type': content_type}
        self._payload = payload
        self.text = '' if payload is None else str(payload)

    def json(self):
        if self._payload is None:
            raise ValueError("No JSON payload")
        return self._payload


@pytest.mark.parametrize(
    "status_code",
    [HTTPStatus.BAD_REQUEST, HTTPStatus.UNAUTHORIZED, HTTPStatus.FORBIDDEN],
)
def test_detect_auth_status_codes(status_code):
    """Auth status codes are detected regardless of body."""
    assert AuthenticationException.detect(_FakeResponse(status_code)) is True


def test_detect_non_auth_status_code():
    """Non-auth errors (e.g. 500) are not treated as auth failures."""
    response = _FakeResponse(HTTPStatus.INTERNAL_SERVER_ERROR)
    assert AuthenticationException.detect(response) is False


@pytest.mark.parametrize(
    "payload",
    [
        {"errorCode": 11002},
        {"errorCode": 13027},
        {"message": "Unauthorized token"},
        {"message": "Invalid credentials"},
        {"message": "Username and password do not match"},
    ],
)
def test_detect_auth_like_200_payload(payload):
    """Auth-error payloads returned with HTTP 200 are detected."""
    response = _FakeResponse(HTTPStatus.OK, payload=payload)
    assert AuthenticationException.detect(response) is True


@pytest.mark.parametrize(
    "response",
    [
        _FakeResponse(HTTPStatus.OK, payload={"message": "ok"}),
        _FakeResponse(HTTPStatus.OK, payload=["not", "a", "dict"]),
        _FakeResponse(HTTPStatus.OK, content_type="text/plain"),
        _FakeResponse(HTTPStatus.OK, payload=None),
    ],
)
def test_detect_ok_responses_are_not_auth(response):
    """Ordinary 200 responses (and unparseable bodies) are not auth failures."""
    assert AuthenticationException.detect(response) is False


def test_from_response_carries_status_and_message():
    """``from_response`` preserves the status code and best message."""
    response = _FakeResponse(
        HTTPStatus.UNAUTHORIZED, payload={"message": "Unauthorized token"}
    )
    exc = AuthenticationException.from_response(response)
    assert isinstance(exc, AuthenticationException)
    assert exc.errcode == HTTPStatus.UNAUTHORIZED
    assert exc.message == "Unauthorized token"


class TestRuntimeAuthHandling:
    """Integration tests around ``send_request`` raising the dedicated error."""

    def test_runtime_forbidden_raises_authentication(self, m):
        """A persistent 403 at runtime raises AuthenticationException."""
        m.post(urls.LOGIN, json=LOGIN.post_response_ok())
        m.get(urls.OAUTH_TOKEN, json=OAUTH_CLAIMS.get_response_ok())
        m.get(urls.DEVICES, json=MOCK.response_forbidden(), status=403)

        with pytest.raises(jaraco.abode.AuthenticationException):
            self.client.get_devices()

    def test_auth_error_payload_with_http_200(self, m):
        """An auth-error payload returned with HTTP 200 raises AuthenticationException."""
        m.post(urls.LOGIN, json=LOGIN.post_response_ok())
        m.get(urls.OAUTH_TOKEN, json=OAUTH_CLAIMS.get_response_ok())
        m.get(
            urls.DEVICES,
            json={"errorCode": 11002, "message": "Unauthorized token"},
            status=200,
        )

        with pytest.raises(jaraco.abode.AuthenticationException):
            self.client.get_devices()

    def test_transient_token_expiry_still_recovers(self, m):
        """A single 403 followed by success still recovers via re-login."""
        new_token = "REFRESHED"
        m.post(urls.LOGIN, json=LOGIN.post_response_ok(auth_token=new_token))
        m.get(urls.OAUTH_TOKEN, json=OAUTH_CLAIMS.get_response_ok())
        m.get(urls.DEVICES, json=MOCK.response_forbidden(), status=403)
        m.get(urls.DEVICES, json=DEVICES.EMPTY_DEVICE_RESPONSE)
        m.get(urls.PANEL, json=PANEL.get_response_ok())

        self.client.get_devices()

        assert self.client._token == new_token
