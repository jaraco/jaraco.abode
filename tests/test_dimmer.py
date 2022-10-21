"""Test the Abode device classes."""

import jaraco.abode
import jaraco.abode.helpers.constants as CONST

import pytest

from .mock import login as LOGIN
from .mock import oauth_claims as OAUTH_CLAIMS
from .mock import logout as LOGOUT
from .mock import panel as PANEL
from .mock import devices as DEVICES
from .mock.devices import dimmer as DIMMER


class TestDimmer:
    """Test the light device with a dimmer."""

    def tests_dimmer_device_properties(self, m):
        """Tests that dimmer light devices properties work as expected."""
        # Set up URL's
        m.post(CONST.LOGIN_URL, text=LOGIN.post_response_ok())
        m.get(CONST.OAUTH_TOKEN_URL, text=OAUTH_CLAIMS.get_response_ok())
        m.post(CONST.LOGOUT_URL, text=LOGOUT.post_response_ok())
        m.get(CONST.PANEL_URL, text=PANEL.get_response_ok(mode=CONST.MODE_STANDBY))
        m.get(
            CONST.DEVICES_URL,
            text=DIMMER.device(
                devid=DIMMER.DEVICE_ID,
                status=CONST.STATUS_OFF,
                level=0,
                low_battery=False,
                no_response=False,
            ),
        )

        # Logout to reset everything
        self.abode.logout()

        # Get our dimmer
        device = self.abode.get_device(DIMMER.DEVICE_ID)

        # Test our device
        assert device is not None
        assert device.status == CONST.STATUS_OFF
        assert device.brightness == "0"
        assert device.has_brightness
        assert device.is_dimmable
        assert not device.has_color
        assert not device.is_color_capable
        assert not device.battery_low
        assert not device.no_response
        assert not device.is_on

        # Set up our direct device get url
        device_url = CONST.DEVICE_URL.format(device_id=DIMMER.DEVICE_ID)

        # Change device properties
        m.get(
            device_url,
            text=DIMMER.device(
                devid=DIMMER.DEVICE_ID,
                status=CONST.STATUS_ON,
                level=87,
                low_battery=True,
                no_response=True,
            ),
        )

        # Refesh device and test changes
        device.refresh()

        assert device.status == CONST.STATUS_ON
        assert device.brightness == "87"
        assert device.battery_low
        assert device.no_response
        assert device.is_on

    def tests_dimmer_status_changes(self, m):
        """Tests that dimmer device changes work as expected."""
        # Set up URL's
        m.post(CONST.LOGIN_URL, text=LOGIN.post_response_ok())
        m.get(CONST.OAUTH_TOKEN_URL, text=OAUTH_CLAIMS.get_response_ok())
        m.post(CONST.LOGOUT_URL, text=LOGOUT.post_response_ok())
        m.get(CONST.PANEL_URL, text=PANEL.get_response_ok(mode=CONST.MODE_STANDBY))
        m.get(
            CONST.DEVICES_URL,
            text=DIMMER.device(
                devid=DIMMER.DEVICE_ID,
                status=CONST.STATUS_OFF,
                level=0,
                low_battery=False,
                no_response=False,
            ),
        )

        # Logout to reset everything
        self.abode.logout()

        # Get our dimmer
        device = self.abode.get_device(DIMMER.DEVICE_ID)

        # Test that we have our device
        assert device is not None
        assert device.status == CONST.STATUS_OFF
        assert not device.is_on

        # Set up control url response
        control_url = CONST.BASE_URL + DIMMER.CONTROL_URL
        m.put(
            control_url,
            text=DEVICES.status_put_response_ok(
                devid=DIMMER.DEVICE_ID, status=CONST.STATUS_ON_INT
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
                devid=DIMMER.DEVICE_ID, status=CONST.STATUS_OFF_INT
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
                devid=DIMMER.DEVICE_ID, status=CONST.STATUS_OFF_INT
            ),
        )

        with pytest.raises(jaraco.abode.AbodeException):
            device.switch_on()
