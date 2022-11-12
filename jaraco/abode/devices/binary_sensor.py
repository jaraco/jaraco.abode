"""Abode binary sensor device."""

from typing import Optional, Union, Iterable

from ..devices import Device
from ..helpers import constants as CONST


class BinarySensor(Device):
    """Class to represent an on / off, online/offline sensor."""

    implements: Optional[Union[str, Iterable[str]]] = (
        CONST.TYPE_CONNECTIVITY,
        CONST.TYPE_MOISTURE,
        CONST.TYPE_OPENING,
    )

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
