"""Abode binary sensor device."""

from . import status as STATUS
from . import base


class BinarySensor(base.Device):
    """Class to represent an on / off, online/offline sensor."""

    @property
    def is_on(self):
        """
        Get sensor state.

        Assume offline or open (worst case).
        """
        return self.status not in (
            STATUS.OFF,
            STATUS.OFFLINE,
            STATUS.CLOSED,
        )


class Connectivity(BinarySensor):
    tags = (
        'glass',
        'keypad',
        'remote_controller',
        'siren',
        # status display
        'bx',
        # moisture
        'water_sensor',
    )


class Moisture(BinarySensor):
    pass


class Motion(BinarySensor):
    pass


class Occupancy(BinarySensor):
    @property
    def is_on(self):
        return self.status not in STATUS.ONLINE


class Door(BinarySensor):
    tags = ('door_contact',)
