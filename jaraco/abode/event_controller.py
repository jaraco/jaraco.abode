"""Abode cloud push events."""
import collections
import logging
import http.cookiejar

from jaraco.itertools import always_iterable

import jaraco
from .devices.base import Device
from .devices.alarm import Alarm
from .helpers import urls
from .helpers import errors as ERROR
from .helpers import timeline as TIMELINE
from . import socketio as sio
from ._itertools import single, opt_single

log = logging.getLogger(__name__)

SOCKETIO_URL = 'wss://my.goabode.com/socket.io/'


def _cookie_string(cookies: http.cookiejar.CookieJar):
    """
    >>> jar = http.cookiejar.CookieJar()
    >>> from test.test_http_cookiejar import interact_netscape
    >>> _ = interact_netscape(jar, 'http://any/', 'foo=bar', 'bing=baz')
    >>> _cookie_string(jar) in ['foo=bar; bing=baz', 'bing=baz; foo=bar']
    True
    """
    return "; ".join(f"{cookie.name}={cookie.value}" for cookie in cookies)


class EventController:
    """Subscribes to events."""

    def __init__(self, client, url=SOCKETIO_URL):
        self._client = client
        self._thread = None
        self._running = False
        self._connected = False

        # Setup callback dicts
        self._connection_status_callbacks = collections.defaultdict(list)
        self._device_callbacks = collections.defaultdict(list)
        self._event_callbacks = collections.defaultdict(list)
        self._timeline_callbacks = collections.defaultdict(list)

        # Setup SocketIO
        self._socketio = sio.SocketIO(url=url, origin=urls.BASE)

        # Setup SocketIO Callbacks
        self._socketio.on('started', self._on_socket_started)
        self._socketio.on('connected', self._on_socket_connected)
        self._socketio.on('disconnected', self._on_socket_disconnected)
        self._socketio.on('com.goabode.device.update', self._on_device_update)
        self._socketio.on('com.goabode.gateway.mode', self._on_mode_change)
        self._socketio.on('com.goabode.gateway.timeline', self._on_timeline_update)
        self._socketio.on('com.goabode.automation', self._on_automation_update)

    def start(self):
        """Start a thread to handle Abode SocketIO notifications."""
        self._socketio.start()

    def stop(self):
        """Tell the subscription thread to terminate - will block."""
        self._socketio.stop()

    def add_connection_status_callback(self, unique_id, callback):
        """Register callback for Abode server connection status."""
        if not unique_id:
            return False

        log.debug("Subscribing to Abode connection updates for: %s", unique_id)

        self._connection_status_callbacks[unique_id].append(callback)

        return True

    def remove_connection_status_callback(self, unique_id):
        """Unregister connection status callbacks."""
        if not unique_id:
            return False

        log.debug("Unsubscribing from Abode connection updates for : %s", unique_id)

        self._connection_status_callbacks[unique_id].clear()

        return True

    def add_device_callback(self, devices, callback):
        """Register a device callback."""
        if not devices:
            return False

        for device in always_iterable(devices):
            # Device may be a device_id
            device_id = device

            # If they gave us an actual device, get that devices ID
            if isinstance(device, Device):
                device_id = device.id

            # Validate the device is valid
            if not self._client.get_device(device_id):
                raise jaraco.abode.Exception(ERROR.EVENT_DEVICE_INVALID)

            log.debug("Subscribing to updates for device_id: %s", device_id)

            self._device_callbacks[device_id].append(callback)

        return True

    def remove_all_device_callbacks(self, devices):
        """Unregister all callbacks for a device."""
        if not devices:
            return False

        for device in always_iterable(devices):
            device_id = device

            if isinstance(device, Device):
                device_id = device.id

            if not self._client.get_device(device_id):
                raise jaraco.abode.Exception(ERROR.EVENT_DEVICE_INVALID)

            if device_id not in self._device_callbacks:
                return False

            log.debug("Unsubscribing from all updates for device_id: %s", device_id)

            self._device_callbacks[device_id].clear()

        return True

    def add_event_callback(self, event_groups, callback):
        """Register callback for a group of timeline events."""
        if not event_groups:
            return False

        for event_group in always_iterable(event_groups):
            if event_group not in TIMELINE.Groups.ALL:
                raise jaraco.abode.Exception(ERROR.EVENT_GROUP_INVALID)

            log.debug("Subscribing to event group: %s", event_group)

            self._event_callbacks[event_group].append(callback)

        return True

    def add_timeline_callback(self, timeline_events, callback):
        """Register a callback for a specific timeline event."""
        if not timeline_events:
            return False

        for timeline_event in always_iterable(timeline_events):
            if not isinstance(timeline_event, dict):
                raise jaraco.abode.Exception(ERROR.EVENT_CODE_MISSING)

            event_code = timeline_event.get('event_code')

            if not event_code:
                raise jaraco.abode.Exception(ERROR.EVENT_CODE_MISSING)

            log.debug("Subscribing to timeline event: %s", timeline_event)

            self._timeline_callbacks[event_code].append(callback)

        return True

    @property
    def connected(self):
        """Get the Abode connection status."""
        return self._connected

    @property
    def socketio(self):
        """Get the SocketIO instance."""
        return self._socketio

    def _on_socket_started(self):
        """Socket IO startup callback."""
        self._socketio.set_cookie(_cookie_string(self._client._get_session().cookies))

    def _on_socket_connected(self):
        """Socket IO connected callback."""
        self._connected = True

        try:
            self._client.refresh()
        except Exception as exc:
            log.warning("Captured exception during Abode refresh: %s", exc)
        finally:
            # Callbacks should still execute even if refresh fails (Abode
            # server issues) so that the entity availability in Home Assistant
            # is updated since we are in fact connected to the web socket.
            for callbacks in self._connection_status_callbacks.values():
                for callback in callbacks:
                    _execute_callback(callback)

    def _on_socket_disconnected(self):
        """Socket IO disconnected callback."""
        self._connected = False

        for callbacks in self._connection_status_callbacks.values():
            for callback in callbacks:
                _execute_callback(callback)

    def _on_device_update(self, devid):
        """Device callback from Abode SocketIO server."""
        devid = opt_single(devid)

        if devid is None:
            log.warning("Device update with no device id.")
            return

        log.debug("Device update event for device ID: %s", devid)

        device = self._client.get_device(devid, True)

        if not device:
            log.debug("Got device update for unknown device: %s", devid)
            return

        for callback in self._device_callbacks[device.id]:
            _execute_callback(callback, device)

    def _on_mode_change(self, mode):
        """Mode change broadcast from Abode SocketIO server."""
        mode = opt_single(mode)

        if mode is None:
            log.warning("Mode change event with no mode.")
            return

        if not mode or mode.lower() not in Alarm.all_modes:
            log.warning("Mode change event with unknown mode: %s", mode)
            return

        log.debug("Alarm mode change event to: %s", mode)

        # We're just going to convert it to an Alarm device
        alarm_device = self._client.get_alarm(refresh=True)

        # At the time of development, refreshing after mode change notification
        # didn't seem to get the latest update immediately. As such, we will
        # force the mode status now to match the notification.
        alarm_device._state['mode']['area_1'] = mode

        for callback in self._device_callbacks[alarm_device.id]:
            _execute_callback(callback, alarm_device)

    def _on_timeline_update(self, event):
        """Timeline update broadcast from Abode SocketIO server."""
        event = single(event)

        event_type = event.get('event_type')
        event_code = event.get('event_code')

        if not event_type or not event_code:
            log.warning("Invalid timeline update event: %s", event)
            return

        log.debug(
            "Timeline event received: %s - %s (%s)",
            event.get('event_name'),
            event_type,
            event_code,
        )

        # Compress our callbacks into those that match this event_code
        # or ones registered to get callbacks for all events
        codes = (event_code, TIMELINE.ALL['event_code'])
        all_callbacks = [self._timeline_callbacks[code] for code in codes]

        for callbacks in all_callbacks:
            for callback in callbacks:
                _execute_callback(callback, event)

        # Attempt to map the event code to a group and callback
        event_group = TIMELINE.map_event_code(event_code)

        for callback in self._event_callbacks[event_group]:
            _execute_callback(callback, event)

    def _on_automation_update(self, event):
        """Automation update broadcast from Abode SocketIO server."""
        event_group = TIMELINE.Groups.AUTOMATION_EDIT

        event = single(event)

        for callback in self._event_callbacks[event_group]:
            _execute_callback(callback, event)


def _execute_callback(callback, *args, **kwargs):
    # Callback with some data, capturing any exceptions to prevent chaos
    try:
        callback(*args, **kwargs)
    except Exception as exc:
        log.warning("Captured exception during callback: %s", exc)
