"""Test the Abode device classes."""

import jaraco.abode.helpers.constants as CONST

from .mock import login as LOGIN
from .mock import oauth_claims as OAUTH_CLAIMS
from .mock import logout as LOGOUT
from .mock import panel as PANEL
from .mock.devices import lm as LM


class TestLM:
    """Test the sensor class/LM."""

    def tests_cover_lm_properties(self, m):
        """Tests that sensor/LM devices properties work as expected."""
        # Set up URL's
        m.post(CONST.LOGIN_URL, text=LOGIN.post_response_ok())
        m.get(CONST.OAUTH_TOKEN_URL, text=OAUTH_CLAIMS.get_response_ok())
        m.post(CONST.LOGOUT_URL, text=LOGOUT.post_response_ok())
        m.get(CONST.PANEL_URL, text=PANEL.get_response_ok(mode=CONST.MODE_STANDBY))
        m.get(
            CONST.DEVICES_URL,
            text=LM.device(
                devid=LM.DEVICE_ID,
                status='72 °F',
                temp='72 °F',
                lux='14 lx',
                humidity='34 %',
                low_battery=False,
                no_response=False,
            ),
        )

        # Logout to reset everything
        self.abode.logout()

        # Get our power switch
        device = self.abode.get_device(LM.DEVICE_ID)

        # Test our device
        assert device is not None
        assert device.status == '72 °F'
        assert not device.battery_low
        assert not device.no_response
        assert device.has_temp
        assert device.has_humidity
        assert device.has_lux
        assert device.temp == 72
        assert device.temp_unit == '°F'
        assert device.humidity == 34
        assert device.humidity_unit == '%'
        assert device.lux == 14
        assert device.lux_unit == 'lux'

        # Set up our direct device get url
        device_url = CONST.DEVICE_URL.format(device_id=LM.DEVICE_ID)

        # Change device properties
        m.get(
            device_url,
            text=LM.device(
                devid=LM.DEVICE_ID,
                status='12 °C',
                temp='12 °C',
                lux='100 lx',
                humidity='100 %',
                low_battery=True,
                no_response=True,
            ),
        )

        # Refesh device and test changes
        device.refresh()

        assert device.status == '12 °C'
        assert device.battery_low
        assert device.no_response
        assert device.has_temp
        assert device.has_humidity
        assert device.has_lux
        assert device.temp == 12
        assert device.temp_unit == '°C'
        assert device.humidity == 100
        assert device.humidity_unit == '%'
        assert device.lux == 100
        assert device.lux_unit == 'lux'

    def tests_lm_float_units(self, m):
        """Tests that sensor/LM devices properties work as expected."""
        # Set up URL's
        m.post(CONST.LOGIN_URL, text=LOGIN.post_response_ok())
        m.get(CONST.OAUTH_TOKEN_URL, text=OAUTH_CLAIMS.get_response_ok())
        m.post(CONST.LOGOUT_URL, text=LOGOUT.post_response_ok())
        m.get(CONST.PANEL_URL, text=PANEL.get_response_ok(mode=CONST.MODE_STANDBY))
        m.get(
            CONST.DEVICES_URL,
            text=LM.device(
                devid=LM.DEVICE_ID,
                status='72.23 °F',
                temp='72.23 °F',
                lux='14.11 lx',
                humidity='34.38 %',
                low_battery=False,
                no_response=False,
            ),
        )

        # Logout to reset everything
        self.abode.logout()

        # Get our power switch
        device = self.abode.get_device(LM.DEVICE_ID)

        # Test our device
        assert device is not None
        assert device.status == '72.23 °F'
        assert not device.battery_low
        assert not device.no_response
        assert device.has_temp
        assert device.has_humidity
        assert device.has_lux
        assert device.temp == 72.23
        assert device.temp_unit == '°F'
        assert device.humidity == 34.38
        assert device.humidity_unit == '%'
        assert device.lux == 14.11
        assert device.lux_unit == 'lux'

    def tests_lm_temp_only(self, m):
        """Tests that sensor/LM devices properties work as expected."""
        # Set up URL's
        m.post(CONST.LOGIN_URL, text=LOGIN.post_response_ok())
        m.get(CONST.OAUTH_TOKEN_URL, text=OAUTH_CLAIMS.get_response_ok())
        m.post(CONST.LOGOUT_URL, text=LOGOUT.post_response_ok())
        m.get(CONST.PANEL_URL, text=PANEL.get_response_ok(mode=CONST.MODE_STANDBY))
        m.get(
            CONST.DEVICES_URL,
            text=LM.device(
                devid=LM.DEVICE_ID, status='72 °F', temp='72 °F', lux='', humidity=''
            ),
        )

        # Logout to reset everything
        self.abode.logout()

        # Get our power switch
        device = self.abode.get_device(LM.DEVICE_ID)

        # Test our device
        assert device is not None
        assert device.status == '72 °F'
        assert device.has_temp
        assert not device.has_humidity
        assert not device.has_lux
        assert device.temp == 72
        assert device.temp_unit == '°F'
        assert device.humidity is None
        assert device.humidity_unit is None
        assert device.lux is None
        assert device.lux_unit is None
