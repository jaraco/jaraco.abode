"""Abode valve device."""

from . import status as STATUS
from .switch import Switch


class Valve(Switch):
    """Class to add valve functionality."""

    tags = ('valve',)

    def switch_on(self):
        """Open the valve."""
        success = self.set_status(STATUS.ON_INT)

        if success:
            self._state['status'] = STATUS.OPEN

        return success

    def switch_off(self):
        """Close the valve."""
        success = self.set_status(STATUS.OFF_INT)

        if success:
            self._state['status'] = STATUS.CLOSED

        return success

    @property
    def is_on(self):
        """
        Get switch state.

        Assume switch is on.
        """
        return self.status not in (STATUS.CLOSED, STATUS.OFFLINE)

    @property
    def is_dimmable(self):
        """Device dimmable."""
        return False
