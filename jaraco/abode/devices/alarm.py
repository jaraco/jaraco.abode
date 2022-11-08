"""Abode alarm device."""
import logging
import copy

from ..exceptions import AbodeException

from ..devices.switch import AbodeDevice, AbodeSwitch
from ..helpers import constants as CONST
from ..helpers import errors as ERROR

_LOGGER = logging.getLogger(__name__)


def state_from_panel(panel_state, area='1'):
    """Adapt panel state to alarm state."""
    alarm_state = copy.deepcopy(panel_state)
    alarm_state['name'] = CONST.ALARM_NAME
    alarm_state['id'] = CONST.ALARM_DEVICE_ID + area
    alarm_state['type'] = CONST.ALARM_TYPE
    alarm_state['type_tag'] = CONST.DEVICE_ALARM
    alarm_state['generic_type'] = CONST.TYPE_ALARM
    alarm_state['uuid'] = alarm_state.get('mac').replace(':', '').lower()
    return alarm_state


def create_alarm(panel_json, abode, area='1'):
    """Create a new alarm device from a panel response."""
    return AbodeAlarm(state_from_panel(panel_json), abode, area)


class AbodeAlarm(AbodeSwitch):
    """Class to represent the Abode alarm as a device."""

    def __init__(self, json_obj, abode, area='1'):
        """Set up Abode alarm device."""
        super().__init__(json_obj, abode)
        self._area = area

    def set_mode(self, mode):
        """Set Abode alarm mode."""
        if not mode:
            raise AbodeException(ERROR.MISSING_ALARM_MODE)

        if mode.lower() not in CONST.ALL_MODES:
            raise AbodeException(ERROR.INVALID_ALARM_MODE, CONST.ALL_MODES)

        mode = mode.lower()

        response = self._abode.send_request(
            "put", CONST.get_panel_mode_url(self._area, mode)
        )

        _LOGGER.debug("Set Alarm Home Response: %s", response.text)

        response_object = response.json()

        if response_object['area'] != self._area:
            raise AbodeException(ERROR.SET_MODE_AREA)

        if response_object['mode'] != mode:
            raise AbodeException(ERROR.SET_MODE_MODE)

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
        return self.set_mode(self._abode.default_mode)

    def switch_off(self):
        """Arm Abode to home mode."""
        return self.set_standby()

    def refresh(self, url=CONST.PANEL_URL):
        """Refresh the alarm device."""
        response_object = AbodeDevice.refresh(self, url)

        self._abode._panel.update(response_object[0])

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
