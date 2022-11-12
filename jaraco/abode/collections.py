"""Collection routines."""

from collections.abc import Mapping, MutableMapping


def update(target: MutableMapping, merge: Mapping) -> MutableMapping:
    """Recursively merge items from merge into target."""
    for key, value in merge.items():
        recurse = key in target and isinstance(target[key], Mapping)
        target[key] = update(target[key], value) if recurse else value
    return target
