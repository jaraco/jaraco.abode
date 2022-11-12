"""Collection routines."""

from collections.abc import Mapping, MutableMapping


def update(dct: MutableMapping, dct_merge: Mapping) -> MutableMapping:
    """Recursively merge dct_merge into dct."""
    for key, value in dct_merge.items():
        if key in dct and isinstance(dct[key], Mapping):
            dct[key] = update(dct[key], value)
        else:
            dct[key] = value
    return dct
