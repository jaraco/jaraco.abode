"""Abode sensor device."""
import re

from .binary_sensor import BinarySensor


class Sensor(BinarySensor):
    """Class to represent a sensor device."""

    keys = {'temperature', 'humidity', 'lux'}

    @classmethod
    def is_sensor(cls, state):
        statuses = state.get('statuses', {})
        return any(key in statuses for key in cls.keys)

    def _get_status(self, key):
        return self._state.get('statuses', {}).get(key)

    def _get_numeric_status(self, key):
        """Extract the numeric value from the statuses object."""
        value = self._get_status(key)

        if value and any(i.isdigit() for i in value):
            return float(re.sub("[^0-9.]", "", value))

    @property
    def temp(self):
        """Get device temp."""
        return self._get_numeric_status('temperature')

    @property
    def temp_unit(self):
        """Get unit of temp."""
        if '°F' in self._get_status('temperature'):
            return '°F'

        if '°C' in self._get_status('temperature'):
            return '°C'

    @property
    def humidity(self):
        """Get device humdity."""
        return self._get_numeric_status('humidity')

    @property
    def humidity_unit(self):
        """Get unit of humidity."""
        if '%' in self._get_status('humidity'):
            return '%'

    @property
    def lux(self):
        """Get device lux."""
        return self._get_numeric_status('lux')

    @property
    def lux_unit(self):
        """Get unit of lux."""
        if 'lx' in self._get_status('lux'):
            return 'lux'

    @property
    def has_temp(self):
        """Device reports temperature."""
        return self.temp is not None

    @property
    def has_humidity(self):
        """Device reports humidity level."""
        return self.humidity is not None

    @property
    def has_lux(self):
        """Device reports light lux level."""
        return self.lux is not None
