import functools
import importlib

import importlib_resources as resources
from bx_py_utils.compat import removesuffix


@functools.lru_cache()
def import_all():
    """Import all modules from this package."""
    device_mods = (
        removesuffix(mod.name, '.py')
        for mod in resources.files(__package__).iterdir()
        if mod.name != '__init__.py'
    )
    for mod in device_mods:
        importlib.import_module(f'.{mod}', __package__)
