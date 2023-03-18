"""Abode cover device."""

from . import status as STATUS
from .switch import Switch


class Cover(Switch):
    """Class to add cover functionality."""

    tags = ('secure_barrier',)

    def switch_on(self):
        """Turn the switch on."""
        self.set_status(int(STATUS.OPEN))
        self._state['status'] = STATUS.OPEN

    def switch_off(self):
        """Turn the switch off."""
        self.set_status(int(STATUS.CLOSED))
        self._state['status'] = STATUS.CLOSED

    def open_cover(self):
        """Open the cover."""
        return self.switch_on()

    def close_cover(self):
        """Close the cover."""
        return self.switch_off()

    @property
    def is_open(self):
        """Get if the cover is open."""
        return self.is_on

    @property
    def is_on(self):
        """
        Get cover state.

        Assume cover is open.
        """
        return self.status not in STATUS.CLOSED
