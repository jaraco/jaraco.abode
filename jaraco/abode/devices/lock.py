"""Abode lock device."""

from . import status as STATUS
from . import base


class Lock(base.Device):
    """Class to represent a door lock."""

    tags = ('door_lock',)

    def lock(self):
        """Lock the device."""
        success = self.set_status(int(STATUS.Lock.CLOSED))

        if success:
            self._state['status'] = STATUS.Lock.CLOSED

        return success

    def unlock(self):
        """Unlock the device."""
        success = self.set_status(int(STATUS.Lock.OPEN))

        if success:
            self._state['status'] = STATUS.Lock.OPEN

        return success

    @property
    def is_locked(self):
        """
        Get locked state.

        Err on side of caution, assume if lock isn't closed then it's open.
        """
        return self.status in STATUS.Lock.CLOSED
