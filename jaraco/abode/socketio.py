"""Small SocketIO client via Websockets."""
import collections
import json
import logging
import threading
import random
import itertools
import contextlib
import datetime
import urllib.parse

from lomond import WebSocket
from lomond import events
from lomond.persist import persist
from lomond.errors import WebSocketError
import jaraco.collections

from .exceptions import SocketIOException
from .helpers import errors as ERRORS


log = logging.getLogger(__name__)


class EngineIO:
    codes = jaraco.collections.BijectiveMap(
        open=0,
        close=1,
        ping=2,
        pong=3,
        message=4,
    )


class BackoffIntervals:
    """
    >>> bi = BackoffIntervals()
    >>> intervals = list(itertools.islice(bi, 10))
    >>> all(
    ...     BackoffIntervals.min_wait <= interval <= BackoffIntervals.max_wait
    ...     for interval in intervals)
    True
    """

    min_wait = 5
    max_wait = 30
    diff = max_wait - min_wait

    def __init__(self):
        self.reset(1)

    def __iter__(self):
        return self

    def __next__(self):
        attempt = next(self.attempts)
        return self.min_wait + random.random() * min(self.diff, 2**attempt)

    def reset(self, *args):
        self.attempts = itertools.count(*args)


def find_json_list(text):
    r"""
    >>> find_json_list('["foo",\n\t"bar"]')
    ['foo', 'bar']
    >>> find_json_list('{"abc": ["123"]}')
    ['123']
    >>> find_json_list('{"abc": null}')
    Traceback (most recent call last):
    ...
    ValueError: ...
    >>> find_json_list('some text string')
    Traceback (most recent call last):
    ...
    ValueError: ...
    """
    l_bracket = text.find("[")
    r_bracket = text.rfind("]")

    if l_bracket == -1 or r_bracket == -1:
        raise ValueError("No list found", text)

    return json.loads(text[l_bracket : r_bracket + 1])


class SocketIO:
    """Class for using websockets to talk to a SocketIO server."""

    codes = jaraco.collections.BijectiveMap(
        connect=0,
        disconnect=1,
        event=2,
        error=4,
    )

    def __init__(self, url, cookie=None, origin=None):
        params = dict(EIO=3, transport='websocket')
        self._url = url + '?' + urllib.parse.urlencode(params)

        self._cookie = cookie
        self._origin = origin

        self._thread = None
        self._websocket = None
        self._exit_event = None
        self._running = False

        self._websocket_connected = False
        self._engineio_connected = False
        self._socketio_connected = False

        self._last_ping_time = datetime.datetime.min
        self._last_packet_time = datetime.datetime.min

        self._callbacks = collections.defaultdict(list)

    def set_origin(self, origin=None):
        """Set the Origin header."""
        self._origin = origin

    def set_cookie(self, cookie=None):
        """Set the Cookie header."""
        self._cookie = cookie

    def on(self, event_name, callback):
        """Register callback for a SocketIO event."""
        log.debug("Adding callback for event name: %s", event_name)
        self._callbacks[event_name].append(callback)

    def start(self):
        """Start a thread to handle SocketIO notifications."""
        if self._thread:
            return

        log.info("Starting SocketIO thread...")

        self._thread = threading.Thread(
            target=self._run, name='SocketIOThread', daemon=True
        )
        self._thread.start()

    def stop(self):
        """Tell the SocketIO thread to terminate."""
        if not self._thread:
            return

        log.info("Stopping SocketIO thread...")

        self._running = False

        if self._exit_event:
            self._exit_event.set()

        self._thread.join()

    def _run(self):
        self._running = True

        intervals = BackoffIntervals()

        while self._running:
            log.info("Attempting to connect to SocketIO server...")

            try:
                self._step(intervals)
            except SocketIOException as exc:
                log.warning("SocketIO Error: %s", exc.details)
            except WebSocketError as exc:
                log.warning("Websocket Error: %s", exc)

            if not self._running:
                break

            interval = next(intervals)
            log.info("Waiting %f seconds before reconnecting...", interval)
            if self._exit_event.wait(interval):
                break

        self._handle_event('stopped', None)

    def _add_header(self, name, value):
        if value is None:
            return
        self._websocket.add_header(name.encode(), value.encode())

    def _step(self, intervals):
        self._handle_event('started')

        self._websocket = WebSocket(self._url)
        self._exit_event = threading.Event()

        self._add_header('Cookie', self._cookie)
        self._add_header('Origin', self._origin)

        for event in persist(
            self._websocket, ping_rate=0, poll=5.0, exit_event=self._exit_event
        ):
            if isinstance(event, events.Connected):
                intervals.reset()

            name = event.__class__.__name__.lower()
            with contextlib.suppress(AttributeError):
                handler = getattr(self, f'_on_websocket_{name}')
                handler(event)

            if self._running is False:
                self._websocket.close()

    def _on_websocket_connected(self, _event):
        self._websocket_connected = True
        log.info("Websocket Connected")
        self._handle_event('connected')

    def _on_websocket_disconnected(self, _event):
        self._websocket_connected = False
        self._engineio_connected = False
        self._socketio_connected = False

        log.info("Websocket Disconnected")
        self._handle_event('disconnected')

    def _on_websocket_poll(self, _event):
        last_packet_delta = datetime.datetime.now() - self._last_packet_time

        if self._engineio_connected and last_packet_delta > self._ping_timeout:
            log.warning("SocketIO Server Ping Timeout")
            self._websocket.close()
            return

        last_ping_delta = datetime.datetime.now() - self._last_ping_time

        if self._engineio_connected and last_ping_delta >= self._ping_interval:
            self._websocket.send_text(str(EngineIO.codes['ping']))
            self._last_ping_time = datetime.datetime.now()
            log.debug("Client Ping")
            self._handle_event('ping')

        self._handle_event('poll')

    def _on_websocket_text(self, _event):
        self._last_packet_time = datetime.datetime.now()

        log.debug("Received: %s", _event.text)

        code = int(_event.text[:1])
        message = _event.text[1:]

        try:
            name = EngineIO.codes[code]
            handler = getattr(self, f'_on_engineio_{name}')
            handler(message)
        except KeyError:
            log.debug("Ignoring unrecognized EngineIO packet")

    def _on_websocket_backoff(self, _event):
        return

    def _on_engineio_open(self, message):
        packet = json.loads(message)

        self._ping_interval = datetime.timedelta(milliseconds=packet['pingInterval'])
        log.debug("Set ping interval to %s", self._ping_interval)

        self._ping_timeout = datetime.timedelta(milliseconds=packet['pingTimeout'])
        log.debug("Set ping timeout to %s", self._ping_timeout)

        self._engineio_connected = True
        log.debug("EngineIO Connected")

    def _on_engineio_close(self, message):
        self._engineio_connected = False
        log.debug("EngineIO Disconnected")
        self._websocket.close()

    def _on_engineio_pong(self, message):
        log.debug("Server Pong")
        self._handle_event('pong')

    def _on_engineio_message(self, message):
        code = int(message[:1])
        data = message[1:]

        try:
            name = SocketIO.codes[code]
            handler = getattr(self, f'_on_socketio_{name}')
            handler(data)
        except KeyError:
            log.debug("Ignoring SocketIO message: %s", message)

    def _on_socketio_connected(self):
        self._socketio_connected = True
        log.debug("SocketIO Connected")

    def _on_socketio_disconnected(self):
        self._socketio_connected = False
        log.debug("SocketIO Disconnected")
        self._websocket.close()

    def _on_socketio_error(self, _message_data):
        self._handle_event('error', _message_data)
        raise SocketIOException(ERRORS.SOCKETIO_ERROR, details=_message_data)

    def _on_socketio_event(self, _message_data):
        try:
            json_data = find_json_list(_message_data)
        except ValueError:
            log.warning("Unable to find event [data]: %s", _message_data)
            return
        self._handle_event('event', _message_data)
        self._handle_event(json_data[0], json_data[1:])

    def _handle_event(self, event_name, *args):
        for callback in self._callbacks[event_name]:
            try:
                callback(*args)
            except Exception as exc:
                log.exception(
                    "Captured exception during SocketIO event callback: %s", exc
                )
