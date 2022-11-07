import logging

from jaraco.collections import DictAdapter, Projection

from ..exceptions import AbodeException

from ..helpers import constants as CONST
from ..helpers import errors as ERROR
from .control import needs_control_url


_LOGGER = logging.getLogger(__name__)


class AbodeDevice:
    """Class to represent each Abode device."""

    def __init__(self, state, abode):
        """Set up Abode device."""
        self._state = state
        self._abode = abode

    def __getattr__(self, name):
        if name in '_name _type _type_tag _generic_type'.split():
            name = name.lstrip('_')

        try:
            return self._state[name]
        except KeyError as exc:
            raise AttributeError(name) from exc

    @property
    def _device_id(self):
        return self.id

    @property
    def _device_uuid(self):
        return self.uuid

    @needs_control_url
    def set_status(self, status):
        """Set device status."""
        path = self._state['control_url']

        status_data = {'status': str(status)}

        response = self._abode.send_request(method="put", path=path, data=status_data)
        response_object = response.json()

        _LOGGER.debug("Set Status Response: %s", response.text)

        if response_object['id'] != self.device_id:
            raise AbodeException(ERROR.SET_STATUS_DEV_ID)

        if response_object['status'] != str(status):
            raise AbodeException(ERROR.SET_STATUS_STATE)

        # Note: Status result is of int type, not of new status of device.
        # Seriously, why would you do that?
        # So, can't set status here must be done at device level.

        _LOGGER.info("Set device %s status to: %s", self.device_id, status)

    @needs_control_url
    def set_level(self, level):
        """Set device level."""
        url = self._state['control_url']

        level_data = {'level': str(level)}

        response = self._abode.send_request("put", url, data=level_data)
        response_object = response.json()

        _LOGGER.debug("Set Level Response: %s", response.text)

        if response_object['id'] != self.device_id:
            raise AbodeException(ERROR.SET_STATUS_DEV_ID)

        if response_object['level'] != str(level):
            raise AbodeException(ERROR.SET_STATUS_STATE)

        self.update(response_object)

        _LOGGER.info("Set device %s level to: %s", self.device_id, level)

    def get_value(self, name):
        """Get a value from the json object.

        This is the common data and is the best place to get state
        from if it has the data you require.
        This data is updated by the subscription service.
        """
        return self._state.get(name.lower(), {})

    def refresh(self, path=CONST.DEVICE_URL):
        """Refresh the devices json object data.

        Only needed if you're not using the notification service.
        """
        path = path.format(device_id=self.device_id)

        response = self._abode.send_request(method="get", path=path)
        response_object = response.json()

        _LOGGER.debug("Device Refresh Response: %s", response.text)

        if response_object and not isinstance(response_object, (tuple, list)):
            response_object = [response_object]

        for device in response_object:
            self.update(device)

        return response_object

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
        fallback = f'{self.type} {self.device_id}'
        return self._state.get('name') or fallback

    @property
    def generic_type(self):
        """Get the generic type of this device."""
        return self._generic_type

    @property
    def type(self):
        """Get the type of this device."""
        return self._type

    @property
    def type_tag(self):
        """Get the type tag of this device."""
        return self._type_tag

    @property
    def device_id(self):
        """Get the device id."""
        return self._device_id

    @property
    def device_uuid(self):
        """Get the device uuid."""
        return self._device_uuid

    @property
    def desc(self):
        """Get a short description of the device."""
        tmpl = '{name} (ID: {device_id}, UUID: {device_uuid}) - {type} - {status}'
        return tmpl.format_map(DictAdapter(self))
