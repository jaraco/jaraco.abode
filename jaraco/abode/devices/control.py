import functools


def needs_control_url(orig):
    @functools.wraps(orig)
    def wrapper(self, *args, **kwargs):
        if not self._state['control_url']:
            return False
        orig(self, *args, **kwargs)
        return True

    return wrapper
