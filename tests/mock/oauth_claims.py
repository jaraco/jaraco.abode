"""Mock Abode Claims Response."""

import json

from . import OAUTH_TOKEN


def get_response_ok(oauth_token=OAUTH_TOKEN):
    """Return the oauth2 claims token."""
    return json.dumps(
        dict(token_type='Bearer', access_token=oauth_token, expires_in=3600)
    )
