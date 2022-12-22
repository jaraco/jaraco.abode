"""Mock Abode Logout Response."""


def post_response_ok():
    """Return the successful logout response json."""
    return dict(code=200, message='Logout successful.')


def post_response_bad_request():
    """Return the failed logout response json."""
    return dict(code=400, message='Some logout error occurred.', detail=None)
