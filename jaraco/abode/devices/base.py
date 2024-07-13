import logging
import warnings
from typing import Tuple

import jaraco.abode
from jaraco.classes.ancestry import iter_subclasses

from ..helpers import errors as ERROR
from ..helpers import urls
from ..state import Stateful
from . import pkg

log = logging.getLogger(__name__)


class Device(Stateful):
    """Class to represent each Abode device."""

    tags: Tuple[str, ...] = ()
    """
    Each device has a ``type_tag``, something like "device_type.door_lock".
    Each Device subclass declares the tags that it services (with the
    "device_type." prefix omitted).
    """
    _desc_t = '{name} (ID: {id}, UUID: {uuid}) - {type} - {status}'
    _url_t = urls.DEVICE

    @property
    def _control_url(self):
        if not self._state['control_url']:
            raise jaraco.abode.Exception(("Control URL required",))
        return self._state['control_url']

    def set_status(self, status) -> None:
        """Set device status."""
        response = self._client.send_request(
            method="put",
            path=self._control_url,
            data={'status': str(status)},
        )
        response_object = response.json()

        log.debug("Set Status Response: %s", response.text)

        if response_object['id'] != self.id:
            raise jaraco.abode.Exception(ERROR.SET_STATUS_DEV_ID)

        if response_object['status'] != str(status):
            raise jaraco.abode.Exception(ERROR.SET_STATUS_STATE)

        # Note: Status returned is a string of int (e.g. "0") and not
        # the string indication normally passed for the status (e.g.
        # "LockClosed"), so can't be used to update self._state.

        log.info("Set device %s status to: %s", self.id, status)

    def set_level(self, level) -> None:
        """Set device level."""
        response = self._client.send_request(
            "put",
            self._control_url,
            data={'level': str(level)},
        )
        response_object = response.json()

        log.debug("Set Level Response: %s", response.text)

        if response_object['id'] != self.id:
            raise jaraco.abode.Exception(ERROR.SET_STATUS_DEV_ID)

        if response_object['level'] != str(level):
            raise jaraco.abode.Exception(ERROR.SET_STATUS_STATE)

        self.update(response_object)

        log.info("Set device %s level to: %s", self.id, level)

    def get_value(self, name):
        """Get a value from the device state."""
        return self._state.get(name.lower(), {})

    @property
    def status(self):
        """Shortcut to get the generic status of a device."""
        return self.get_value('status')

    @property
    def battery_low(self):
        """Is battery level low."""
        return bool(self.get_value('faults').get('low_battery', 0))

    @property
    def no_response(self):
        """Is the device responding."""
        return bool(self.get_value('faults').get('no_response', 0))

    @property
    def out_of_order(self):
        """Is the device out of order."""
        return bool(self.get_value('faults').get('out_of_order', 0))

    @property
    def tampered(self):
        """Has the device been tampered with."""
        # 'tempered' - Typo in API?
        return bool(self.get_value('faults').get('tempered', 0))

    @property
    def name(self):
        """Get the name of this device."""
        fallback = f'{self.type} {self.id}'
        return self._state.get('name') or fallback

    @property
    def device_id(self):
        """Get the device id."""
        warnings.warn(
            "Device.device_id is deprecated. Use .id.", DeprecationWarning, stacklevel=2
        )
        return self.id

    @property
    def device_uuid(self):
        """Get the device uuid."""
        warnings.warn(
            "Device.device_uuid is deprecated. Use .uuid.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.uuid

    @classmethod
    def new(cls, state, client):
        """Create new device object for the given type."""
        pkg.import_all()
        try:
            type_tag = state['type_tag']
        except KeyError as exc:
            raise jaraco.abode.Exception(ERROR.UNABLE_TO_MAP_DEVICE) from exc

        return cls.resolve_class(type_tag)(state, client)

    @property
    def generic_type(self):
        return self.__class__.__name__.lower()

    @classmethod
    def by_type(cls):
        return {sub_cls.__name__.lower(): sub_cls for sub_cls in iter_subclasses(cls)}

    @classmethod
    def resolve_class(cls, type_tag):
        """
        >>> Device.resolve_class('device_type.povs')
        <class 'jaraco.abode.devices.binary_sensor.Motion'>
        """
        lookup = {
            f'device_type.{tag}': sub_cls
            for sub_cls in reversed(tuple(iter_subclasses(cls)))
            for tag in sub_cls.tags
        }
        return lookup.get(type_tag.lower(), Unknown)


class Unknown(Device):
    pass
