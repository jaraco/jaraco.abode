"""Abode binary sensor device."""

from ..helpers import constants as CONST
from . import base


class BinarySensor(base.Device):
    """Class to represent an on / off, online/offline sensor."""

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


class Connectivity(BinarySensor):
    pass


class Moisture(BinarySensor):
    pass


class Motion(BinarySensor):
    pass


class Occupancy(BinarySensor):
    pass


class Door(BinarySensor):
    pass
