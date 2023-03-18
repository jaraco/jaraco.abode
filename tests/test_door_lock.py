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
from .mock.devices import door_lock as DOOR_LOCK


class TestDoorLock:
    """Test the door lock."""

    def test_lock_device_properties(self, m):
        """Tests that lock devices properties work as expected."""
        # Set up URLs
        m.post(urls.LOGIN, json=LOGIN.post_response_ok())
        m.get(urls.OAUTH_TOKEN, json=OAUTH_CLAIMS.get_response_ok())
        m.post(urls.LOGOUT, json=LOGOUT.post_response_ok())
        m.get(urls.PANEL, json=PANEL.get_response_ok(mode='standby'))
        m.get(
            urls.DEVICES,
            json=DOOR_LOCK.device(
                devid=DOOR_LOCK.DEVICE_ID,
                status=STATUS.Lock.CLOSED,
                low_battery=False,
                no_response=False,
            ),
        )

        # Logout to reset everything
        self.client.logout()

        # Get our lock
        device = self.client.get_device(DOOR_LOCK.DEVICE_ID)

        # Test our device
        assert device is not None
        assert device.status == STATUS.Lock.CLOSED
        assert not device.battery_low
        assert not device.no_response
        assert device.is_locked

        # Set up our direct device get url
        device_url = urls.DEVICE.format(id=DOOR_LOCK.DEVICE_ID)

        # Change device properties
        m.get(
            device_url,
            json=DOOR_LOCK.device(
                devid=DOOR_LOCK.DEVICE_ID,
                status=STATUS.Lock.OPEN,
                low_battery=True,
                no_response=True,
            ),
        )

        # Refesh device and test changes
        device.refresh()

        assert device.status == STATUS.Lock.OPEN
        assert device.battery_low
        assert device.no_response
        assert not device.is_locked

    def test_lock_device_mode_changes(self, m):
        """Tests that lock device changes work as expected."""
        # Set up URLs
        m.post(urls.LOGIN, json=LOGIN.post_response_ok())
        m.get(urls.OAUTH_TOKEN, json=OAUTH_CLAIMS.get_response_ok())
        m.post(urls.LOGOUT, json=LOGOUT.post_response_ok())
        m.get(urls.PANEL, json=PANEL.get_response_ok(mode='standby'))
        m.get(
            urls.DEVICES,
            json=DOOR_LOCK.device(
                devid=DOOR_LOCK.DEVICE_ID,
                status=STATUS.Lock.CLOSED,
                low_battery=False,
                no_response=False,
            ),
        )

        # Logout to reset everything
        self.client.logout()

        # Get our power switch
        device = self.client.get_device(DOOR_LOCK.DEVICE_ID)

        # Test that we have our device
        assert device is not None
        assert device.status == STATUS.Lock.CLOSED
        assert device.is_locked

        # Set up control url response
        control_url = urls.BASE + DOOR_LOCK.CONTROL_URL
        m.put(
            control_url,
            json=DEVICES.status_put_response_ok(
                devid=DOOR_LOCK.DEVICE_ID, status=int(STATUS.Lock.OPEN)
            ),
        )

        # Change the mode to "on"
        device.unlock()
        assert device.status == STATUS.Lock.OPEN
        assert not device.is_locked

        # Change response
        m.put(
            control_url,
            json=DEVICES.status_put_response_ok(
                devid=DOOR_LOCK.DEVICE_ID, status=int(STATUS.Lock.CLOSED)
            ),
        )

        # Change the mode to "off"
        device.lock()
        assert device.status == STATUS.Lock.CLOSED
        assert device.is_locked

        # Test that an invalid status response throws exception
        m.put(
            control_url,
            json=DEVICES.status_put_response_ok(
                devid=DOOR_LOCK.DEVICE_ID, status=int(STATUS.Lock.CLOSED)
            ),
        )

        with pytest.raises(jaraco.abode.Exception):
            device.unlock()
