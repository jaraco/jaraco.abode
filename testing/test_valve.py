"""Test the Abode device classes."""

import pytest

import jaraco.abode
from jaraco.abode.helpers import urls
import jaraco.abode.helpers.constants as CONST

from .mock import login as LOGIN
from .mock import oauth_claims as OAUTH_CLAIMS
from .mock import logout as LOGOUT
from .mock import panel as PANEL
from .mock import devices as DEVICES
from .mock.devices import valve as VALVE


class TestValve:
    """Test the valve."""

    def test_switch_device_properties(self, m):
        """Tests that switch devices properties work as expected."""
        # Set up URLs
        m.post(urls.LOGIN, json=LOGIN.post_response_ok())
        m.get(urls.OAUTH_TOKEN, json=OAUTH_CLAIMS.get_response_ok())
        m.post(urls.LOGOUT, json=LOGOUT.post_response_ok())
        m.get(urls.PANEL, json=PANEL.get_response_ok(mode=CONST.MODE_STANDBY))
        m.get(
            urls.DEVICES,
            json=VALVE.device(
                devid=VALVE.DEVICE_ID,
                status=CONST.STATUS_CLOSED,
                low_battery=False,
                no_response=False,
            ),
        )

        # Logout to reset everything
        self.client.logout()

        # Get our power switch
        device = self.client.get_device(VALVE.DEVICE_ID)

        # Test our device
        assert device is not None
        assert device.status == CONST.STATUS_CLOSED
        assert not device.battery_low
        assert not device.no_response
        assert not device.is_on
        assert not device.is_dimmable

        # Set up our direct device get url
        device_url = urls.DEVICE.format(device_id=VALVE.DEVICE_ID)

        # Change device properties
        m.get(
            device_url,
            json=VALVE.device(
                devid=VALVE.DEVICE_ID,
                status=CONST.STATUS_OPEN,
                low_battery=True,
                no_response=True,
            ),
        )

        # Refesh device and test changes
        device.refresh()

        assert device.status == CONST.STATUS_OPEN
        assert device.battery_low
        assert device.no_response
        assert device.is_on

    def test_switch_status_changes(self, m):
        """Tests that switch device changes work as expected."""
        # Set up URLs
        m.post(urls.LOGIN, json=LOGIN.post_response_ok())
        m.get(urls.OAUTH_TOKEN, json=OAUTH_CLAIMS.get_response_ok())
        m.post(urls.LOGOUT, json=LOGOUT.post_response_ok())
        m.get(urls.PANEL, json=PANEL.get_response_ok(mode=CONST.MODE_STANDBY))
        m.get(
            urls.DEVICES,
            json=VALVE.device(
                devid=VALVE.DEVICE_ID,
                status=CONST.STATUS_CLOSED,
                low_battery=False,
                no_response=False,
            ),
        )

        # Logout to reset everything
        self.client.logout()

        # Get our power switch
        device = self.client.get_device(VALVE.DEVICE_ID)

        # Test that we have our device
        assert device is not None
        assert device.status == CONST.STATUS_CLOSED
        assert not device.is_on

        # Set up control url response
        control_url = urls.BASE + VALVE.CONTROL_URL
        m.put(
            control_url,
            json=DEVICES.status_put_response_ok(
                devid=VALVE.DEVICE_ID, status=CONST.STATUS_OPEN_INT
            ),
        )

        # Change the mode to "on"
        assert device.switch_on()
        assert device.status == CONST.STATUS_OPEN
        assert device.is_on

        # Change response
        m.put(
            control_url,
            json=DEVICES.status_put_response_ok(
                devid=VALVE.DEVICE_ID, status=CONST.STATUS_CLOSED_INT
            ),
        )

        # Change the mode to "off"
        assert device.switch_off()
        assert device.status == CONST.STATUS_CLOSED
        assert not device.is_on

        # Test that an invalid status response throws exception
        m.put(
            control_url,
            json=DEVICES.status_put_response_ok(
                devid=VALVE.DEVICE_ID, status=CONST.STATUS_CLOSED_INT
            ),
        )

        with pytest.raises(jaraco.abode.Exception):
            device.switch_on()
