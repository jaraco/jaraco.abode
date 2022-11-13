"""Abode valve device."""

from ..helpers import constants as CONST
from .switch import Switch


class Valve(Switch):
    """Class to add valve functionality."""

    implements = CONST.TYPE_VALVE

    def switch_on(self):
        """Open the valve."""
        success = self.set_status(CONST.STATUS_ON_INT)

        if success:
            self._state['status'] = CONST.STATUS_OPEN

        return success

    def switch_off(self):
        """Close the valve."""
        success = self.set_status(CONST.STATUS_OFF_INT)

        if success:
            self._state['status'] = CONST.STATUS_CLOSED

        return success

    @property
    def is_on(self):
        """
        Get switch state.

        Assume switch is on.
        """
        return self.status not in (CONST.STATUS_CLOSED, CONST.STATUS_OFFLINE)

    @property
    def is_dimmable(self):
        """Device dimmable."""
        return False
