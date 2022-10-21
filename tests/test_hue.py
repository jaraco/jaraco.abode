"""Test the Abode device classes."""

import pytest

import jaraco.abode
import jaraco.abode.helpers.constants as CONST

from .mock import login as LOGIN
from .mock import oauth_claims as OAUTH_CLAIMS
from .mock import logout as LOGOUT
from .mock import panel as PANEL
from .mock import devices as DEVICES
from .mock.devices import hue as HUE


class TestHue:
    """Test the light device with Hue."""

    def tests_hue_device_properties(self, m):
        """Tests that hue light devices properties work as expected."""
        # Set up URL's
        m.post(CONST.LOGIN_URL, text=LOGIN.post_response_ok())
        m.get(CONST.OAUTH_TOKEN_URL, text=OAUTH_CLAIMS.get_response_ok())
        m.post(CONST.LOGOUT_URL, text=LOGOUT.post_response_ok())
        m.get(CONST.PANEL_URL, text=PANEL.get_response_ok(mode=CONST.MODE_STANDBY))
        m.get(
            CONST.DEVICES_URL,
            text=HUE.device(
                devid=HUE.DEVICE_ID,
                status=CONST.STATUS_OFF,
                level=0,
                saturation=57,
                hue=60,
                color_temp=6536,
                color_mode=CONST.COLOR_MODE_ON,
                low_battery=False,
                no_response=False,
            ),
        )

        # Logout to reset everything
        self.abode.logout()

        # Get our dimmer
        device = self.abode.get_device(HUE.DEVICE_ID)

        # Test our device
        assert device is not None
        assert device.status == CONST.STATUS_OFF
        assert device.brightness == "0"
        assert device.color == (60, 57)  # (hue, saturation)
        assert device.color_temp == 6536
        assert device.has_brightness
        assert device.is_dimmable
        assert device.has_color
        assert device.is_color_capable
        assert not device.battery_low
        assert not device.no_response
        assert not device.is_on

        # Set up our direct device get url
        device_url = CONST.DEVICE_URL.format(device_id=HUE.DEVICE_ID)

        # Change device properties
        m.get(
            device_url,
            text=HUE.device(
                devid=HUE.DEVICE_ID,
                status=CONST.STATUS_ON,
                level=45,
                saturation=22,
                hue=104,
                color_temp=4000,
                color_mode=CONST.COLOR_MODE_OFF,
                low_battery=True,
                no_response=True,
            ),
        )

        # Refesh device and test changes
        device.refresh()

        assert device.status == CONST.STATUS_ON
        assert device.color == (104, 22)  # (hue, saturation)
        assert device.color_temp == 4000
        assert device.has_brightness
        assert device.is_dimmable
        assert not device.has_color
        assert device.is_color_capable
        assert device.battery_low
        assert device.no_response
        assert device.is_on

    def tests_hue_status_changes(self, m):
        """Tests that hue device changes work as expected."""
        # Set up URL's
        m.post(CONST.LOGIN_URL, text=LOGIN.post_response_ok())
        m.get(CONST.OAUTH_TOKEN_URL, text=OAUTH_CLAIMS.get_response_ok())
        m.post(CONST.LOGOUT_URL, text=LOGOUT.post_response_ok())
        m.get(CONST.PANEL_URL, text=PANEL.get_response_ok(mode=CONST.MODE_STANDBY))
        m.get(
            CONST.DEVICES_URL,
            text=HUE.device(
                devid=HUE.DEVICE_ID,
                status=CONST.STATUS_OFF,
                level=0,
                saturation=57,
                hue=60,
                color_temp=6536,
                color_mode=CONST.COLOR_MODE_ON,
                low_battery=False,
                no_response=False,
            ),
        )

        # Logout to reset everything
        self.abode.logout()

        # Get our hue device
        device = self.abode.get_device(HUE.DEVICE_ID)

        # Test that we have our device
        assert device is not None
        assert device.status == CONST.STATUS_OFF
        assert not device.is_on

        # Set up control url response
        control_url = CONST.BASE_URL + HUE.CONTROL_URL
        m.put(
            control_url,
            text=DEVICES.status_put_response_ok(
                devid=HUE.DEVICE_ID, status=CONST.STATUS_ON_INT
            ),
        )

        # Change the mode to "on"
        assert device.switch_on()
        assert device.status == CONST.STATUS_ON
        assert device.is_on

        # Change response
        m.put(
            control_url,
            text=DEVICES.status_put_response_ok(
                devid=HUE.DEVICE_ID, status=CONST.STATUS_OFF_INT
            ),
        )

        # Change the mode to "off"
        assert device.switch_off()
        assert device.status == CONST.STATUS_OFF
        assert not device.is_on

        # Test that an invalid status response throws exception
        m.put(
            control_url,
            text=DEVICES.status_put_response_ok(
                devid=HUE.DEVICE_ID, status=CONST.STATUS_OFF_INT
            ),
        )

        with pytest.raises(jaraco.abode.AbodeException):
            device.switch_on()

    def tests_hue_color_temp_changes(self, m):
        """Tests that hue device color temp changes work as expected."""
        # Set up URL's
        m.post(CONST.LOGIN_URL, text=LOGIN.post_response_ok())
        m.get(CONST.OAUTH_TOKEN_URL, text=OAUTH_CLAIMS.get_response_ok())
        m.post(CONST.LOGOUT_URL, text=LOGOUT.post_response_ok())
        m.get(CONST.PANEL_URL, text=PANEL.get_response_ok(mode=CONST.MODE_STANDBY))
        m.get(
            CONST.DEVICES_URL,
            text=HUE.device(
                devid=HUE.DEVICE_ID,
                status=CONST.STATUS_OFF,
                level=0,
                saturation=57,
                hue=60,
                color_temp=6536,
                color_mode=CONST.COLOR_MODE_ON,
                low_battery=False,
                no_response=False,
            ),
        )

        # Logout to reset everything
        self.abode.logout()

        # Get our hue device
        device = self.abode.get_device(HUE.DEVICE_ID)

        # Test that we have our device
        assert device is not None
        assert device.status == CONST.STATUS_OFF
        assert not device.is_on
        assert device.color_temp == 6536

        # Set up integrations url response
        m.post(
            HUE.INTEGRATIONS_URL,
            text=HUE.color_temp_post_response_ok(devid=HUE.DEVICE_ID, color_temp=5554),
        )

        # Change the color temp
        assert device.set_color_temp(5554)
        assert device.color_temp == 5554

        # Change response
        m.post(
            HUE.INTEGRATIONS_URL,
            text=HUE.color_temp_post_response_ok(devid=HUE.DEVICE_ID, color_temp=4434),
        )

        # Change the color to something that mismatches
        assert device.set_color_temp(4436)

        # Assert that the color is set to the response color
        assert device.color_temp == 4434

        # Test that an invalid ID in response throws exception
        m.post(
            HUE.INTEGRATIONS_URL,
            text=HUE.color_temp_post_response_ok(
                devid=(HUE.DEVICE_ID + "23"), color_temp=4434
            ),
        )

        with pytest.raises(jaraco.abode.AbodeException):
            device.set_color_temp(4434)

    def tests_hue_color_changes(self, m):
        """Tests that hue device color changes work as expected."""
        # Set up URL's
        m.post(CONST.LOGIN_URL, text=LOGIN.post_response_ok())
        m.get(CONST.OAUTH_TOKEN_URL, text=OAUTH_CLAIMS.get_response_ok())
        m.post(CONST.LOGOUT_URL, text=LOGOUT.post_response_ok())
        m.get(CONST.PANEL_URL, text=PANEL.get_response_ok(mode=CONST.MODE_STANDBY))
        m.get(
            CONST.DEVICES_URL,
            text=HUE.device(
                devid=HUE.DEVICE_ID,
                status=CONST.STATUS_OFF,
                level=0,
                saturation=57,
                hue=60,
                color_temp=6536,
                color_mode=CONST.COLOR_MODE_ON,
                low_battery=False,
                no_response=False,
            ),
        )

        # Logout to reset everything
        self.abode.logout()

        # Get our hue device
        device = self.abode.get_device(HUE.DEVICE_ID)

        # Test that we have our device
        assert device is not None
        assert device.status == CONST.STATUS_OFF
        assert not device.is_on
        assert device.color == (60, 57)  # (hue, saturation)

        # Set up integrations url response
        m.post(
            HUE.INTEGRATIONS_URL,
            text=HUE.color_post_response_ok(devid=HUE.DEVICE_ID, hue=70, saturation=80),
        )

        # Change the color temp
        assert device.set_color((70, 80))
        assert device.color == (70, 80)  # (hue, saturation)

        # Change response
        m.post(
            HUE.INTEGRATIONS_URL,
            text=HUE.color_post_response_ok(devid=HUE.DEVICE_ID, hue=55, saturation=85),
        )

        # Change the color to something that mismatches
        assert device.set_color((44, 44))

        # Assert that the color is set to the response color
        assert device.color == (55, 85)  # (hue, saturation)

        # Test that an invalid ID in response throws exception
        m.post(
            HUE.INTEGRATIONS_URL,
            text=HUE.color_post_response_ok(
                devid=(HUE.DEVICE_ID + "23"), hue=55, saturation=85
            ),
        )

        with pytest.raises(jaraco.abode.AbodeException):
            device.set_color((44, 44))
