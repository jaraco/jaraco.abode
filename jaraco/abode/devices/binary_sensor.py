"""Abode binary sensor device."""

from typing import Optional, Union, Iterable

from ..helpers import constants as CONST
from . import base


class BinarySensor(base.Device):
    """Class to represent an on / off, online/offline sensor."""

    implements: Optional[Union[str, Iterable[str]]] = CONST.BINARY_SENSOR_TYPES

    @property
    def is_on(self):
        """
        Get sensor state.

        Assume offline or open (worst case).
        """
        if self._type == 'Occupancy':
            return self.status not in CONST.STATUS_ONLINE
        return self.status not in (
            CONST.STATUS_OFF,
            CONST.STATUS_OFFLINE,
            CONST.STATUS_CLOSED,
        )
