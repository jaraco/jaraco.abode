"""Abode valve device."""

from . import status as STATUS
from .switch import Switch


class Valve(Switch):
    """Class to add valve functionality."""

    tags = ('valve',)

    def switch_on(self) -> None:
        """Open the valve."""
        self.set_status(int(STATUS.ON))
        self._state['status'] = STATUS.OPEN

    def switch_off(self) -> None:
        """Close the valve."""
        self.set_status(int(STATUS.OFF))
        self._state['status'] = STATUS.CLOSED

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
