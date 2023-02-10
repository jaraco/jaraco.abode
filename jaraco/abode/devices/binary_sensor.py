"""Abode binary sensor device."""

from ..helpers import constants as CONST
from . import base


class BinarySensor(base.Device):
    """Class to represent an on / off, online/offline sensor."""

    _BinarySensor_types = [
        'connectivity',
        'moisture',
        'motion',
        'occupancy',
        'door',
    ]

    @property
    def is_on(self):
        """
        Get sensor state.

        Assume offline or open (worst case).
        """
        if self.type == 'Occupancy':
            return self.status not in CONST.STATUS_ONLINE
        return self.status not in (
            CONST.STATUS_OFF,
            CONST.STATUS_OFFLINE,
            CONST.STATUS_CLOSED,
        )
