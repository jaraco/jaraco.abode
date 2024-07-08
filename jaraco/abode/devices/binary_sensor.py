"""Abode binary sensor device."""

from . import base
from . import status as STATUS


class BinarySensor(base.Device):
    """Class to represent an on / off, online/offline sensor."""

    @property
    def is_on(self):
        """
        Get sensor state.

        Assume offline or open (worst case).
        """
        if self.type == 'Occupancy':
            return self.status not in STATUS.ONLINE
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


class Motion(BinarySensor):
    # These device types are all considered 'occupancy' but could apparently
    # also be multi-sensors based on their state.
    tags = (
        'room_sensor',
        'temperature_sensor',
        # LM = LIGHT MOTION?
        'lm',
        'pir',
        'povs',
    )

    @classmethod
    def specialize(cls, state):
        from . import sensor

        new_type = sensor.Sensor if sensor.Sensor.is_sensor(state) else cls
        state['generic_type'] = new_type.__name__.lower()
        return new_type


class Door(BinarySensor):
    tags = ('door_contact',)
