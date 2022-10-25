"""Abode light device."""
import logging
import math

from ..exceptions import AbodeException

from ..devices.switch import AbodeSwitch
from ..helpers import constants as CONST
from ..helpers import errors as ERROR
from .control import needs_control_url


_LOGGER = logging.getLogger(__name__)


class AbodeLight(AbodeSwitch):
    """Class for lights (dimmers)."""

    @needs_control_url
    def set_color_temp(self, color_temp):
        """Set device color."""
        url = CONST.INTEGRATIONS_URL + self._device_uuid

        color_data = {
            'action': 'setcolortemperature',
            'colorTemperature': int(color_temp),
        }

        response = self._abode.send_request("post", url, data=color_data)
        response_object = response.json()

        _LOGGER.debug("Set Color Temp Response: %s", response.text)

        if response_object['idForPanel'] != self.device_id:
            raise AbodeException(ERROR.SET_STATUS_DEV_ID)

        if response_object['colorTemperature'] != int(color_temp):
            _LOGGER.warning(
                (
                    "Set color temp mismatch for device %s. "
                    "Request val: %s, Response val: %s "
                ),
                self.device_id,
                color_temp,
                response_object['colorTemperature'],
            )

            color_temp = response_object['colorTemperature']

        self.update({'statuses': {'color_temp': color_temp}})

        _LOGGER.info("Set device %s color_temp to: %s", self.device_id, color_temp)

    @needs_control_url
    def set_color(self, color):
        """Set device color."""
        url = CONST.INTEGRATIONS_URL + self._device_uuid

        hue, saturation = color
        color_data = {
            'action': 'setcolor',
            'hue': int(hue),
            'saturation': int(saturation),
        }

        response = self._abode.send_request("post", url, data=color_data)
        response_object = response.json()

        _LOGGER.debug("Set Color Response: %s", response.text)

        if response_object['idForPanel'] != self.device_id:
            raise AbodeException(ERROR.SET_STATUS_DEV_ID)

        # Abode will sometimes return hue value off by 1 (rounding error)
        hue_comparison = math.isclose(response_object["hue"], int(hue), abs_tol=1)
        if not hue_comparison or (response_object["saturation"] != int(saturation)):
            _LOGGER.warning(
                (
                    "Set color mismatch for device %s. "
                    "Request val: %s, Response val: %s "
                ),
                self.device_id,
                (hue, saturation),
                (response_object['hue'], response_object['saturation']),
            )

            hue = response_object['hue']
            saturation = response_object['saturation']

        self.update({'statuses': {'hue': hue, 'saturation': saturation}})

        _LOGGER.info("Set device %s color to: %s", self.device_id, (hue, saturation))

    @property
    def brightness(self):
        """Get light brightness."""
        return self.get_value(CONST.STATUSES_KEY).get('level')

    @property
    def color_temp(self):
        """Get light color temp."""
        return self.get_value(CONST.STATUSES_KEY).get('color_temp')

    @property
    def color(self):
        """Get light color."""
        return (
            self.get_value(CONST.STATUSES_KEY).get('hue'),
            self.get_value(CONST.STATUSES_KEY).get('saturation'),
        )

    @property
    def has_brightness(self):
        """Device has brightness."""
        return self.brightness

    @property
    def has_color(self):
        """Device is using color mode."""
        if self.get_value(CONST.STATUSES_KEY).get('color_mode') == str(
            CONST.COLOR_MODE_ON
        ):
            return True
        return False

    @property
    def is_color_capable(self):
        """Device is color compatible."""
        return 'RGB' in self._type

    @property
    def is_dimmable(self):
        """Device is dimmable."""
        return 'Dimmer' in self._type
