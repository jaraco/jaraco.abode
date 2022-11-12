"""Collection routines."""

import collections.abc


def update(dct, dct_merge):
    """Recursively merge dct_merge into dct."""
    for key, value in dct_merge.items():
        if key in dct and isinstance(dct[key], collections.abc.Mapping):
            dct[key] = update(dct[key], value)
        else:
            dct[key] = value
    return dct
