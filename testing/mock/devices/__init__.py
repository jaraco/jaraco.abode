"""
Mock devices that mimic actual data from Abode servers.

This file should be updated any time the Abode server responses
change to confirm this library can still communicate.
"""

from typing import Any, List


EMPTY_DEVICE_RESPONSE: List[Any] = []


def status_put_response_ok(devid, status):
    """Return status change response json."""
    return dict(id=devid, status=str(status))


def level_put_response_ok(devid, level):
    """Return level change response json."""
    return dict(id=devid, level=str(level))
