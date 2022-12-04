"""Abode alarm device."""
import logging
import copy

import jaraco.abode
from .switch import Switch
from ..helpers import constants as CONST
from ..helpers import errors as ERROR
from ..helpers import urls

_LOGGER = logging.getLogger(__name__)


def id(area):
    return f'area_{area}'


def state_from_panel(panel_state, area='1'):
    """Adapt panel state to alarm state."""
    alarm_state = copy.deepcopy(panel_state)
    alarm_state['name'] = 'Abode Alarm'
    alarm_state['id'] = id(area)
    alarm_state['type'] = 'Alarm'
    alarm_state['type_tag'] = CONST.DEVICE_ALARM
    alarm_state['generic_type'] = CONST.TYPE_ALARM
    alarm_state['uuid'] = alarm_state.get('mac').replace(':', '').lower()
    return alarm_state


def create_alarm(panel_json, abode, area='1'):
    """Create a new alarm device from a panel response."""
    return Alarm(state_from_panel(panel_json), abode, area)


class Alarm(Switch):
    """Class to represent the Abode alarm as a device."""

    implements = CONST.TYPE_ALARM

    def __init__(self, json_obj, abode, area='1'):
        """Set up Abode alarm device."""
        super().__init__(json_obj, abode)
        self._area = area

    def set_mode(self, mode):
        """Set Abode alarm mode."""
        if not mode:
            raise jaraco.abode.Exception(ERROR.MISSING_ALARM_MODE)

        if mode.lower() not in CONST.ALL_MODES:
            raise jaraco.abode.Exception(ERROR.INVALID_ALARM_MODE, CONST.ALL_MODES)

        mode = mode.lower()

        response = self._client.send_request("put", urls.panel_mode(self._area, mode))

        _LOGGER.debug("Set Alarm Home Response: %s", response.text)

        response_object = response.json()

        if response_object['area'] != self._area:
            raise jaraco.abode.Exception(ERROR.SET_MODE_AREA)

        if response_object['mode'] != mode:
            raise jaraco.abode.Exception(ERROR.SET_MODE_MODE)

        self._state['mode'][(self.device_id)] = response_object['mode']

        _LOGGER.info(
            "Set alarm %s mode to: %s", self._device_id, response_object['mode']
        )

        return True

    def set_home(self):
        """Arm Abode to home mode."""
        return self.set_mode(CONST.MODE_HOME)

    def set_away(self):
        """Arm Abode to home mode."""
        return self.set_mode(CONST.MODE_AWAY)

    def set_standby(self):
        """Arm Abode to stay mode."""
        return self.set_mode(CONST.MODE_STANDBY)

    def switch_on(self):
        """Arm Abode to default mode."""
        return self.set_mode(self._client.default_mode)

    def switch_off(self):
        """Arm Abode to home mode."""
        return self.set_standby()

    def refresh(self, url=urls.PANEL):
        """Refresh the alarm device."""
        response_object = super().refresh(url)

        self._client._panel.update(response_object[0])

        return response_object

    def update(self, state):
        super().update(state_from_panel(state, area=self._area))

    @property
    def is_on(self):
        """Is alarm armed."""
        return self.mode in (CONST.MODE_HOME, CONST.MODE_AWAY)

    @property
    def is_standby(self):
        """Is alarm in standby mode."""
        return self.mode == CONST.MODE_STANDBY

    @property
    def is_home(self):
        """Is alarm in home mode."""
        return self.mode == CONST.MODE_HOME

    @property
    def is_away(self):
        """Is alarm in away mode."""
        return self.mode == CONST.MODE_AWAY

    @property
    def mode(self):
        """Get alarm mode."""
        mode = self.get_value('mode').get(self.device_id, None)

        return mode.lower()

    @property
    def status(self):
        """To match existing property."""
        return self.mode

    @property
    def battery(self):
        """Return true if base station on battery backup."""
        return int(self._state.get('battery', '0')) == 1

    @property
    def is_cellular(self):
        """Return true if base station on cellular backup."""
        return int(self._state.get('is_cellular', '0')) == 1

    @property
    def mac_address(self):
        """Get the hub mac address."""
        return self._state.get('mac')
