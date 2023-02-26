"""Test the Abode event controller class."""
from unittest.mock import call, Mock

import pytest

import jaraco.abode
from jaraco.abode.helpers import urls
import jaraco.abode.devices.status as STATUS
import jaraco.abode.helpers.timeline as TIMELINE
from jaraco.abode.devices.binary_sensor import BinarySensor

from .mock import login as LOGIN
from .mock import oauth_claims as OAUTH_CLAIMS
from .mock import logout as LOGOUT
from .mock import panel as PANEL
from .mock.devices import secure_barrier as COVER
from .mock.devices import door_contact as DOORCONTACT
from .mock.devices import ir_camera as IRCAMERA


class TestEventController:
    """Test the event controller."""

    def test_device_id_registration(self, m):
        """Tests that we can register for device events with a device id."""
        # Set up URLs
        m.post(urls.LOGIN, json=LOGIN.post_response_ok())
        m.get(urls.OAUTH_TOKEN, json=OAUTH_CLAIMS.get_response_ok())
        m.post(urls.LOGOUT, json=LOGOUT.post_response_ok())
        m.get(urls.PANEL, json=PANEL.get_response_ok(mode='standby'))
        m.get(
            urls.DEVICES,
            json=COVER.device(
                devid=COVER.DEVICE_ID,
                status=STATUS.CLOSED,
                low_battery=False,
                no_response=False,
            ),
        )

        # Logout to reset everything
        self.client.logout()

        # Get our device
        device = self.client.get_device(COVER.DEVICE_ID)
        assert device is not None

        # Get the event controller
        events = self.client.events
        assert events is not None

        # Create mock callback
        callback = Mock()

        # Register our device id
        assert events.add_device_callback(device.id, callback)

    def test_device_registration(self, m):
        """Tests that we can register for device events with a device."""
        # Set up URLs
        m.post(urls.LOGIN, json=LOGIN.post_response_ok())
        m.get(urls.OAUTH_TOKEN, json=OAUTH_CLAIMS.get_response_ok())
        m.post(urls.LOGOUT, json=LOGOUT.post_response_ok())
        m.get(urls.PANEL, json=PANEL.get_response_ok(mode='standby'))
        m.get(
            urls.DEVICES,
            json=COVER.device(
                devid=COVER.DEVICE_ID,
                status=STATUS.CLOSED,
                low_battery=False,
                no_response=False,
            ),
        )

        # Logout to reset everything
        self.client.logout()

        # Get our device
        device = self.client.get_device(COVER.DEVICE_ID)
        assert device is not None

        # Get the event controller
        events = self.client.events
        assert events is not None

        # Register our device
        assert events.add_device_callback(device, lambda device: None)

    def test_device_all_unregistration(self, m):
        """Tests that we can unregister for all device events."""
        # Set up URLs
        m.post(urls.LOGIN, json=LOGIN.post_response_ok())
        m.get(urls.OAUTH_TOKEN, json=OAUTH_CLAIMS.get_response_ok())
        m.post(urls.LOGOUT, json=LOGOUT.post_response_ok())
        m.get(urls.PANEL, json=PANEL.get_response_ok(mode='standby'))
        m.get(
            urls.DEVICES,
            json=COVER.device(
                devid=COVER.DEVICE_ID,
                status=STATUS.CLOSED,
                low_battery=False,
                no_response=False,
            ),
        )

        # Logout to reset everything
        self.client.logout()

        # Get our device
        device = self.client.get_device(COVER.DEVICE_ID)
        assert device is not None

        # Get the event controller
        events = self.client.events
        assert events is not None

        # Register our device
        assert events.add_device_callback(device, lambda device: None)

        # Unregister all callbacks
        assert events.remove_all_device_callbacks(device)

    def test_invalid_device(self, m):
        """Tests that invalid devices are not registered."""
        # Set up URLs
        m.post(urls.LOGIN, json=LOGIN.post_response_ok())
        m.get(urls.OAUTH_TOKEN, json=OAUTH_CLAIMS.get_response_ok())
        m.post(urls.LOGOUT, json=LOGOUT.post_response_ok())
        m.get(urls.PANEL, json=PANEL.get_response_ok(mode='standby'))
        m.get(
            urls.DEVICES,
            json=COVER.device(
                devid=COVER.DEVICE_ID,
                status=STATUS.CLOSED,
                low_battery=False,
                no_response=False,
            ),
        )

        # Logout to reset everything
        self.client.logout()

        # Get our device
        device = self.client.get_device(COVER.DEVICE_ID)
        assert device is not None

        # Get the event controller
        events = self.client.events
        assert events is not None

        # Create mock callback
        callback = Mock()

        # Test that no device returns false
        assert not events.add_device_callback(None, callback)

        # Create a fake device and attempt to register that
        fake_device = BinarySensor(DOORCONTACT.device(), self.client)

        with pytest.raises(jaraco.abode.Exception):
            events.add_device_callback(fake_device, callback)

    def test_invalid_all_device_unregister(self, m):
        """Tests that invalid devices are not all unregistered."""
        # Set up URLs
        m.post(urls.LOGIN, json=LOGIN.post_response_ok())
        m.get(urls.OAUTH_TOKEN, json=OAUTH_CLAIMS.get_response_ok())
        m.post(urls.LOGOUT, json=LOGOUT.post_response_ok())
        m.get(urls.PANEL, json=PANEL.get_response_ok(mode='standby'))
        m.get(
            urls.DEVICES,
            json=COVER.device(
                devid=COVER.DEVICE_ID,
                status=STATUS.CLOSED,
                low_battery=False,
                no_response=False,
            ),
        )

        # Logout to reset everything
        self.client.logout()

        # Get our device
        device = self.client.get_device(COVER.DEVICE_ID)
        assert device is not None

        # Get the event controller
        events = self.client.events
        assert events is not None

        # Test that no device returns false
        assert not events.remove_all_device_callbacks(None)

        # Create a fake device and attempt to unregister that
        fake_device = BinarySensor(DOORCONTACT.device(), self.client)

        with pytest.raises(jaraco.abode.Exception):
            events.remove_all_device_callbacks(fake_device)

    def test_event_registration(self):
        """Tests that events register correctly."""
        # Get the event controller
        events = self.client.events
        assert events is not None

        # Create mock callback
        callback = Mock()

        # Test that a valid event registers
        assert events.add_event_callback(TIMELINE.Groups.ALARM, callback)

        # Test that no event group returns false
        assert not events.add_event_callback(None, callback)

        # Test that an invalid event throws exception
        with pytest.raises(jaraco.abode.Exception):
            events.add_event_callback("lol", callback)

    def test_timeline_registration(self):
        """Tests that timeline events register correctly."""
        # Get the event controller
        events = self.client.events
        assert events is not None

        # Create mock callback
        callback = Mock()

        # Test that a valid timeline event registers
        assert events.add_timeline_callback(TIMELINE.CAPTURE_IMAGE, callback)

        # Test that no timeline event returns false
        assert not events.add_timeline_callback(None, callback)

        # Test that an invalid timeline event string throws exception
        with pytest.raises(jaraco.abode.Exception):
            events.add_timeline_callback("lol", callback)

        # Test that an invalid timeline event dict throws exception
        with pytest.raises(jaraco.abode.Exception):
            events.add_timeline_callback({"lol": "lol"}, callback)

    def test_device_callback(self, m):
        """Tests that device updates callback correctly."""
        # Set up URLs
        m.post(urls.LOGIN, json=LOGIN.post_response_ok())
        m.get(urls.OAUTH_TOKEN, json=OAUTH_CLAIMS.get_response_ok())
        m.post(urls.LOGOUT, json=LOGOUT.post_response_ok())
        m.get(urls.PANEL, json=PANEL.get_response_ok(mode='standby'))
        m.get(
            urls.DEVICES,
            json=COVER.device(
                devid=COVER.DEVICE_ID,
                status=STATUS.CLOSED,
                low_battery=False,
                no_response=False,
            ),
        )

        # Logout to reset everything
        self.client.logout()

        # Get our device
        device = self.client.get_device(COVER.DEVICE_ID)
        assert device is not None

        # Get the event controller
        events = self.client.events
        assert events is not None

        callback = Mock()

        # Register our device id
        assert events.add_device_callback(device.id, callback)

        # Set up device update URL
        device_url = urls.DEVICE.format(id=COVER.DEVICE_ID)
        m.get(
            device_url,
            json=COVER.device(
                devid=COVER.DEVICE_ID,
                status=STATUS.OPEN,
                low_battery=False,
                no_response=False,
            ),
        )

        # Call our device callback method

        events._on_device_update(device.id)
        callback.assert_called_with(device)

        # Test that our device updated
        assert device.status == STATUS.OPEN

        # Test that no device ID cleanly returns
        events._on_device_update(None)

        # Test that an unknown device cleanly returns
        events._on_device_update(DOORCONTACT.DEVICE_ID)

    def test_events_callback(self):
        """Tests that event updates callback correctly."""
        # Get the event controller
        events = self.client.events
        assert events is not None

        # Create mock callbacks
        capture_callback = Mock()
        alarm_callback = Mock()

        # Register our events
        assert events.add_event_callback(TIMELINE.Groups.CAPTURE, capture_callback)

        assert events.add_event_callback(TIMELINE.Groups.ALARM, alarm_callback)

        # Call our events callback method and trigger a capture group event

        event_json = IRCAMERA.timeline_event()
        events._on_timeline_update(event_json)

        # Our capture callback should get one, but our alarm should not
        capture_callback.assert_called_with(event_json)
        alarm_callback.assert_not_called()

        # Test that an invalid event exits cleanly
        events._on_timeline_update({"invalid": "event"})

    def test_timeline_callback(self):
        """Tests that timeline updates callback correctly."""
        # Get the event controller
        events = self.client.events
        assert events is not None

        # Create mock callbacks
        all_callback = Mock()
        image_callback = Mock()
        opened_callback = Mock()

        # Register our events
        assert events.add_timeline_callback(TIMELINE.ALL, all_callback)

        assert events.add_timeline_callback(TIMELINE.CAPTURE_IMAGE, image_callback)

        assert events.add_timeline_callback(TIMELINE.OPENED, opened_callback)

        # Call our events callback method and trigger an image capture event

        event_json = IRCAMERA.timeline_event()
        events._on_timeline_update(event_json)

        # all and image callbacks should have one, opened none
        all_callback.assert_called_with(event_json)
        image_callback.assert_called_with(event_json)
        opened_callback.assert_not_called()

        # Test that an invalid event exits cleanly
        events._on_timeline_update({"invalid": "event"})

    def test_alarm_callback(self, m):
        """Tests that alarm device updates callback correctly."""
        # Set up URLs
        m.post(urls.LOGIN, json=LOGIN.post_response_ok())
        m.get(urls.OAUTH_TOKEN, json=OAUTH_CLAIMS.get_response_ok())
        m.post(urls.LOGOUT, json=LOGOUT.post_response_ok())
        m.get(urls.PANEL, json=PANEL.get_response_ok(mode='standby'))
        m.get(
            urls.DEVICES,
            json=COVER.device(
                devid=COVER.DEVICE_ID,
                status=STATUS.CLOSED,
                low_battery=False,
                no_response=False,
            ),
        )

        # Logout to reset everything
        self.client.logout()

        # Get our alarm device
        alarm = self.client.get_alarm()
        assert alarm is not None

        # Get the event controller
        events = self.client.events
        assert events is not None

        callback = Mock()

        # Register our alarm for callback
        assert events.add_device_callback(alarm.id, callback)

        # Call our mode changed callback method

        events._on_mode_change('home')
        callback.assert_called_with(alarm)

        # Test that our alarm state is set properly
        assert alarm.mode == 'home'

        # Test that no mode cleanly returns
        events._on_mode_change(None)

        # Test that an unknown mode cleanly returns
        events._on_mode_change("lol")

    def test_execute_callback(self):
        """Tests that callbacks that throw exceptions don't bomb."""
        # Get the event controller
        events = self.client.events
        assert events is not None

        # Create callbacks
        def _callback(event_json):
            raise Exception("CHAOS!!!")

        # Register events callback
        assert events.add_timeline_callback(TIMELINE.CAPTURE_IMAGE, _callback)

        # Call our events callback method and trigger an image capture event

        event_json = IRCAMERA.timeline_event()
        events._on_timeline_update(event_json)

    def test_multi_device_callback(self, m):
        """Tests that multiple device updates callback correctly."""
        # Set up URLs
        m.post(urls.LOGIN, json=LOGIN.post_response_ok())
        m.get(urls.OAUTH_TOKEN, json=OAUTH_CLAIMS.get_response_ok())
        m.post(urls.LOGOUT, json=LOGOUT.post_response_ok())
        m.get(urls.PANEL, json=PANEL.get_response_ok(mode='standby'))
        m.get(
            urls.DEVICES,
            json=[
                COVER.device(
                    devid=COVER.DEVICE_ID,
                    status=STATUS.CLOSED,
                    low_battery=False,
                    no_response=False,
                ),
                DOORCONTACT.device(devid=DOORCONTACT.DEVICE_ID, status=STATUS.CLOSED),
            ],
        )

        # Logout to reset everything
        self.client.logout()

        # Get our devices
        cover = self.client.get_device(COVER.DEVICE_ID)
        assert cover is not None

        doorcontact = self.client.get_device(DOORCONTACT.DEVICE_ID)
        assert doorcontact is not None

        # Get the event controller
        events = self.client.events
        assert events is not None

        callback = Mock()

        # Register our devices
        assert events.add_device_callback([cover, doorcontact], callback)

        # Set up device update URLs
        cover_url = urls.DEVICE.format(id=COVER.DEVICE_ID)
        m.get(
            cover_url,
            json=COVER.device(
                devid=COVER.DEVICE_ID,
                status=STATUS.OPEN,
                low_battery=False,
                no_response=False,
            ),
        )

        door_url = urls.DEVICE.format(id=DOORCONTACT.DEVICE_ID)
        m.get(
            door_url,
            json=DOORCONTACT.device(devid=COVER.DEVICE_ID, status=STATUS.OPEN),
        )

        # Call our device callback method for our cover

        events._on_device_update(cover.id)
        callback.assert_called_with(cover)

        # Test that our device updated
        assert cover.status == STATUS.OPEN

        # Test that our other device didn't update
        assert doorcontact.status == STATUS.CLOSED

        # Call our device callback method for our door contact
        events._on_device_update(doorcontact.id)
        callback.assert_has_calls([call(cover), call(doorcontact)])

        # Test that our door updated now
        assert doorcontact.status == STATUS.OPEN

    def test_multi_events_callback(self):
        """Tests that multiple event updates callback correctly."""
        # Get the event controller
        events = self.client.events
        assert events is not None

        # Create mock callback
        callback = Mock()

        # Register our events
        assert events.add_event_callback(
            [TIMELINE.Groups.ALARM, TIMELINE.Groups.CAPTURE], callback
        )

        # Call our events callback method and trigger a capture group event

        event_json = IRCAMERA.timeline_event()
        events._on_timeline_update(event_json)

        # Ensure our callback was called
        callback.assert_called_with(event_json)

    def test_multi_timeline_callback(self):
        """Tests that multiple timeline updates callback correctly."""
        # Get the event controller
        events = self.client.events
        assert events is not None

        # Create mock callback
        callback = Mock()

        # Register our events
        assert events.add_timeline_callback(
            [TIMELINE.CAPTURE_IMAGE, TIMELINE.OPENED], callback
        )

        # Call our events callback method and trigger a capture group event

        event_json = IRCAMERA.timeline_event()
        events._on_timeline_update(event_json)

        # Ensure our callback was called
        callback.assert_called_with(event_json)

    def test_automations_callback(self):
        """Tests that automation updates callback correctly."""
        # Get the event controller
        events = self.client.events
        assert events is not None

        # Create mock callbacks
        automation_callback = Mock()

        # Register our events
        assert events.add_event_callback(
            TIMELINE.Groups.AUTOMATION_EDIT, automation_callback
        )

        # Call our events callback method and trigger a capture group event

        events._on_automation_update('{}')

        # Our capture callback should get one, but our alarm should not
        automation_callback.assert_called_with('{}')
