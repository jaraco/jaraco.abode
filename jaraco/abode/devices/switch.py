"""Abode switch device."""

from typing import Tuple

from . import status as STATUS
from . import base


class Switch(base.Device):
    """Class to add switch functionality."""

    tags: Tuple[str, ...] = (
        'switch',
        'night_switch',
        'power_switch_sensor',
        'power_switch_meter',
    )

    def switch_on(self):
        """Turn the switch on."""
        self.set_status(int(STATUS.ON))
        self._state['status'] = STATUS.ON

    def switch_off(self):
        """Turn the switch off."""
        self.set_status(int(STATUS.OFF))
        self._state['status'] = STATUS.OFF

    @property
    def is_on(self):
        """
        Get switch state.

        Assume switch is on.
        """
        return self.status not in (STATUS.OFF, STATUS.OFFLINE)

    @property
    def is_dimmable(self):
        """Device dimmable."""
        return False

    @property
    def is_color_capable(self):
        """Device is color compatible."""
        # Prevents issues for switches that are specified as lights
        # in the Abode component of the Home Assistant config file
        return False

    @property
    def has_color(self):
        """Device is using color mode."""
        # Prevents issues for switches that are specified as lights
        # in the Abode component of the Home Assistant config file
        return False
