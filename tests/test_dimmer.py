"""Test the Abode device classes."""

import jaraco.abode
from jaraco.abode.helpers import urls
import jaraco.abode.devices.status as STATUS

import pytest

from .mock import login as LOGIN
from .mock import oauth_claims as OAUTH_CLAIMS
from .mock import logout as LOGOUT
from .mock import panel as PANEL
from .mock import devices as DEVICES
from .mock.devices import dimmer as DIMMER


class TestDimmer:
    """Test the light device with a dimmer."""

    def test_dimmer_device_properties(self, m):
        """Tests that dimmer light devices properties work as expected."""
        # Set up URLs
        m.post(urls.LOGIN, json=LOGIN.post_response_ok())
        m.get(urls.OAUTH_TOKEN, json=OAUTH_CLAIMS.get_response_ok())
        m.post(urls.LOGOUT, json=LOGOUT.post_response_ok())
        m.get(urls.PANEL, json=PANEL.get_response_ok(mode='standby'))
        m.get(
            urls.DEVICES,
            json=DIMMER.device(
                devid=DIMMER.DEVICE_ID,
                status=STATUS.OFF,
                level=0,
                low_battery=False,
                no_response=False,
            ),
        )

        # Logout to reset everything
        self.client.logout()

        # Get our dimmer
        device = self.client.get_device(DIMMER.DEVICE_ID)

        # Test our device
        assert device is not None
        assert device.status == STATUS.OFF
        assert device.brightness == "0"
        assert device.has_brightness
        assert device.is_dimmable
        assert not device.has_color
        assert not device.is_color_capable
        assert not device.battery_low
        assert not device.no_response
        assert not device.is_on

        # Set up our direct device get url
        device_url = urls.DEVICE.format(id=DIMMER.DEVICE_ID)

        # Change device properties
        m.get(
            device_url,
            json=DIMMER.device(
                devid=DIMMER.DEVICE_ID,
                status=STATUS.ON,
                level=87,
                low_battery=True,
                no_response=True,
            ),
        )

        # Refesh device and test changes
        device.refresh()

        assert device.status == STATUS.ON
        assert device.brightness == "87"
        assert device.battery_low
        assert device.no_response
        assert device.is_on

    def test_dimmer_status_changes(self, m):
        """Tests that dimmer device changes work as expected."""
        # Set up URLs
        m.post(urls.LOGIN, json=LOGIN.post_response_ok())
        m.get(urls.OAUTH_TOKEN, json=OAUTH_CLAIMS.get_response_ok())
        m.post(urls.LOGOUT, json=LOGOUT.post_response_ok())
        m.get(urls.PANEL, json=PANEL.get_response_ok(mode='standby'))
        m.get(
            urls.DEVICES,
            json=DIMMER.device(
                devid=DIMMER.DEVICE_ID,
                status=STATUS.OFF,
                level=0,
                low_battery=False,
                no_response=False,
            ),
        )

        # Logout to reset everything
        self.client.logout()

        # Get our dimmer
        device = self.client.get_device(DIMMER.DEVICE_ID)

        # Test that we have our device
        assert device is not None
        assert device.status == STATUS.OFF
        assert not device.is_on

        # Set up control url response
        control_url = urls.BASE + DIMMER.CONTROL_URL
        m.put(
            control_url,
            json=DEVICES.status_put_response_ok(
                devid=DIMMER.DEVICE_ID, status=int(STATUS.ON)
            ),
        )

        # Change the mode to "on"
        device.switch_on()
        assert device.status == STATUS.ON
        assert device.is_on

        # Change response
        m.put(
            control_url,
            json=DEVICES.status_put_response_ok(
                devid=DIMMER.DEVICE_ID, status=int(STATUS.OFF)
            ),
        )

        # Change the mode to "off"
        device.switch_off()
        assert device.status == STATUS.OFF
        assert not device.is_on

        # Test that an invalid status response throws exception
        m.put(
            control_url,
            json=DEVICES.status_put_response_ok(
                devid=DIMMER.DEVICE_ID, status=int(STATUS.OFF)
            ),
        )

        with pytest.raises(jaraco.abode.Exception):
            device.switch_on()
