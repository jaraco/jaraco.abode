"""Abode light device."""
import logging
import math

import jaraco.abode
from ..helpers import errors as ERROR
from ..helpers import urls
from .switch import Switch


log = logging.getLogger(__name__)


class ColorMode:
    on = 0
    off = 2


class Light(Switch):
    """Class for lights (dimmers)."""

    tags = ('dimmer', 'dimmer_meter', 'hue')

    def set_color_temp(self, color_temp) -> None:
        """Set device color."""
        url = urls.INTEGRATIONS + self.uuid

        color_data = {
            'action': 'setcolortemperature',
            'colorTemperature': int(color_temp),
        }

        response = self._client.send_request("post", url, data=color_data)
        response_object = response.json()

        log.debug("Set Color Temp Response: %s", response.text)

        if response_object['idForPanel'] != self.id:
            raise jaraco.abode.Exception(ERROR.SET_STATUS_DEV_ID)

        if response_object['colorTemperature'] != int(color_temp):
            log.warning(
                (
                    "Set color temp mismatch for device %s. "
                    "Request val: %s, Response val: %s "
                ),
                self.id,
                color_temp,
                response_object['colorTemperature'],
            )

            color_temp = response_object['colorTemperature']

        self.update({'statuses': {'color_temp': color_temp}})

        log.info("Set device %s color_temp to: %s", self.id, color_temp)

    def set_color(self, color) -> None:
        """Set device color."""
        url = urls.INTEGRATIONS + self.uuid

        hue, saturation = color
        color_data = {
            'action': 'setcolor',
            'hue': int(hue),
            'saturation': int(saturation),
        }

        response = self._client.send_request("post", url, data=color_data)
        response_object = response.json()

        log.debug("Set Color Response: %s", response.text)

        if response_object['idForPanel'] != self.id:
            raise jaraco.abode.Exception(ERROR.SET_STATUS_DEV_ID)

        # Abode will sometimes return hue value off by 1 (rounding error)
        hue_comparison = math.isclose(response_object["hue"], int(hue), abs_tol=1)
        if not hue_comparison or (response_object["saturation"] != int(saturation)):
            log.warning(
                (
                    "Set color mismatch for device %s. "
                    "Request val: %s, Response val: %s "
                ),
                self.id,
                (hue, saturation),
                (response_object['hue'], response_object['saturation']),
            )

            hue = response_object['hue']
            saturation = response_object['saturation']

        self.update({'statuses': {'hue': hue, 'saturation': saturation}})

        log.info("Set device %s color to: %s", self.id, (hue, saturation))

    @property
    def brightness(self):
        """Get light brightness."""
        return self.get_value('statuses').get('level')

    @property
    def color_temp(self):
        """Get light color temp."""
        return self.get_value('statuses').get('color_temp')

    @property
    def color(self):
        """Get light color."""
        return (
            self.get_value('statuses').get('hue'),
            self.get_value('statuses').get('saturation'),
        )

    @property
    def has_brightness(self):
        """Device has brightness."""
        return self.brightness

    @property
    def has_color(self):
        """Device is using color mode."""
        return self.get_value('statuses').get('color_mode') == str(ColorMode.on)

    @property
    def is_color_capable(self):
        """Device is color compatible."""
        return 'RGB' in self.type

    @property
    def is_dimmable(self):
        """Device is dimmable."""
        return 'Dimmer' in self.type
