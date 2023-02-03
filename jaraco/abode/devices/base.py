import logging
import warnings

from jaraco.collections import DictAdapter, Projection
from jaraco.classes.ancestry import iter_subclasses
from jaraco.itertools import always_iterable

import jaraco
from ..helpers import constants as CONST
from ..helpers import errors as ERROR
from ..helpers import urls
from .control import needs_control_url
from . import pkg


log = logging.getLogger(__name__)


class Device:
    """Class to represent each Abode device."""

    def __init__(self, state, client):
        """Set up Abode device."""
        self._state = state
        self._client = client

    def __getattr__(self, name):
        try:
            return self._state[name]
        except KeyError as exc:
            raise AttributeError(name) from exc

    @needs_control_url
    def set_status(self, status):
        """Set device status."""
        path = self._state['control_url']

        status_data = {'status': str(status)}

        response = self._client.send_request(method="put", path=path, data=status_data)
        response_object = response.json()

        log.debug("Set Status Response: %s", response.text)

        if response_object['id'] != self.id:
            raise jaraco.abode.Exception(ERROR.SET_STATUS_DEV_ID)

        if response_object['status'] != str(status):
            raise jaraco.abode.Exception(ERROR.SET_STATUS_STATE)

        # Note: Status result is of int type, not of new status of device.
        # Seriously, why would you do that?
        # So, can't set status here must be done at device level.

        log.info("Set device %s status to: %s", self.id, status)

    @needs_control_url
    def set_level(self, level):
        """Set device level."""
        url = self._state['control_url']

        level_data = {'level': str(level)}

        response = self._client.send_request("put", url, data=level_data)
        response_object = response.json()

        log.debug("Set Level Response: %s", response.text)

        if response_object['id'] != self.id:
            raise jaraco.abode.Exception(ERROR.SET_STATUS_DEV_ID)

        if response_object['level'] != str(level):
            raise jaraco.abode.Exception(ERROR.SET_STATUS_STATE)

        self.update(response_object)

        log.info("Set device %s level to: %s", self.id, level)

    def get_value(self, name):
        """Get a value from the json object.

        This is the common data and is the best place to get state
        from if it has the data you require.
        This data is updated by the subscription service.
        """
        return self._state.get(name.lower(), {})

    def refresh(self, path=urls.DEVICE):
        """Refresh the devices json object data.

        Only needed if you're not using the notification service.
        """
        path = path.format(device_id=self.id)

        response = self._client.send_request(method="get", path=path)
        state = list(always_iterable(response.json()))

        log.debug("Device Refresh Response: %s", response.text)

        for device in state:
            self.update(device)

        return state

    def update(self, json_state):
        """Update the json data from a dictionary.

        Only updates keys already present.
        """
        self._state.update(Projection(self._state, json_state))

    @property
    def status(self):
        """Shortcut to get the generic status of a device."""
        return self.get_value('status')

    @property
    def battery_low(self):
        """Is battery level low."""
        return bool(int(self.get_value('faults').get('low_battery', '0')))

    @property
    def no_response(self):
        """Is the device responding."""
        return bool(int(self.get_value('faults').get('no_response', '0')))

    @property
    def out_of_order(self):
        """Is the device out of order."""
        return bool(int(self.get_value('faults').get('out_of_order', '0')))

    @property
    def tampered(self):
        """Has the device been tampered with."""
        # 'tempered' - Typo in API?
        return bool(int(self.get_value('faults').get('tempered', '0')))

    @property
    def name(self):
        """Get the name of this device."""
        fallback = f'{self.type} {self.id}'
        return self._state.get('name') or fallback

    @property
    def device_id(self):
        """Get the device id."""
        warnings.warn("Device.device_id is deprecated. Use .id.", DeprecationWarning)
        return self.id

    @property
    def device_uuid(self):
        """Get the device uuid."""
        warnings.warn(
            "Device.device_uuid is deprecated. Use .uuid.", DeprecationWarning
        )
        return self.uuid

    @property
    def desc(self):
        """Get a short description of the device."""
        tmpl = '{name} (ID: {id}, UUID: {uuid}) - {type} - {status}'
        return tmpl.format_map(DictAdapter(self))

    @staticmethod
    def resolve_type_unknown(state):
        if state['generic_type'] != CONST.TYPE_UNKNOWN_SENSOR:
            return

        statuses = state.get(CONST.STATUSES_KEY, {})

        if any(key in statuses for key in CONST.SENSOR_KEYS):
            state['generic_type'] = CONST.TYPE_SENSOR
            return

        version = state.get('version', '')

        state['generic_type'] = (
            CONST.TYPE_OCCUPANCY if version.startswith('MINIPIR') else CONST.TYPE_MOTION
        )

    @classmethod
    def new(cls, state, client):
        """Create new device object for the given type."""
        pkg.import_all()
        try:
            type_tag = state['type_tag']
        except KeyError as exc:
            raise jaraco.abode.Exception(ERROR.UNABLE_TO_MAP_DEVICE) from exc

        state['generic_type'] = CONST.get_generic_type(type_tag.lower())
        cls.resolve_type_unknown(state)
        sensor = cls.by_type().get(state['generic_type'], lambda *args: None)
        return sensor(state, client)

    @classmethod
    def by_type(cls):
        return {
            impl: sub_cls
            for sub_cls in iter_subclasses(cls)
            for impl in always_iterable(sub_cls.implements)
        }
