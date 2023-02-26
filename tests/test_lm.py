"""Test the Abode device classes."""

from jaraco.abode.helpers import urls

from .mock import login as LOGIN
from .mock import oauth_claims as OAUTH_CLAIMS
from .mock import logout as LOGOUT
from .mock import panel as PANEL
from .mock.devices import lm as LM


class TestLM:
    """Test the sensor class/LM."""

    def test_cover_lm_properties(self, m):
        """Tests that sensor/LM devices properties work as expected."""
        # Set up URLs
        m.post(urls.LOGIN, json=LOGIN.post_response_ok())
        m.get(urls.OAUTH_TOKEN, json=OAUTH_CLAIMS.get_response_ok())
        m.post(urls.LOGOUT, json=LOGOUT.post_response_ok())
        m.get(urls.PANEL, json=PANEL.get_response_ok(mode='standby'))
        m.get(
            urls.DEVICES,
            json=LM.device(
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
        self.client.logout()

        # Get our power switch
        device = self.client.get_device(LM.DEVICE_ID)

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
        device_url = urls.DEVICE.format(id=LM.DEVICE_ID)

        # Change device properties
        m.get(
            device_url,
            json=LM.device(
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

    def test_lm_float_units(self, m):
        """Tests that sensor/LM devices properties work as expected."""
        # Set up URLs
        m.post(urls.LOGIN, json=LOGIN.post_response_ok())
        m.get(urls.OAUTH_TOKEN, json=OAUTH_CLAIMS.get_response_ok())
        m.post(urls.LOGOUT, json=LOGOUT.post_response_ok())
        m.get(urls.PANEL, json=PANEL.get_response_ok(mode='standby'))
        m.get(
            urls.DEVICES,
            json=LM.device(
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
        self.client.logout()

        # Get our power switch
        device = self.client.get_device(LM.DEVICE_ID)

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

    def test_lm_temp_only(self, m):
        """Tests that sensor/LM devices properties work as expected."""
        # Set up URLs
        m.post(urls.LOGIN, json=LOGIN.post_response_ok())
        m.get(urls.OAUTH_TOKEN, json=OAUTH_CLAIMS.get_response_ok())
        m.post(urls.LOGOUT, json=LOGOUT.post_response_ok())
        m.get(urls.PANEL, json=PANEL.get_response_ok(mode='standby'))
        m.get(
            urls.DEVICES,
            json=LM.device(
                devid=LM.DEVICE_ID, status='72 °F', temp='72 °F', lux='', humidity=''
            ),
        )

        # Logout to reset everything
        self.client.logout()

        # Get our power switch
        device = self.client.get_device(LM.DEVICE_ID)

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
