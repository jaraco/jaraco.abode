"""
An Abode alarm Python library.
"""

import logging
import uuid
import functools

from more_itertools import consume
from requests_toolbelt import sessions
from requests.exceptions import RequestException
from jaraco.net.http import cookies
from jaraco.functools import retry
from jaraco.itertools import always_iterable
from jaraco.collections import Everything

import jaraco
from .automation import Automation
from .event_controller import EventController
from .exceptions import AuthenticationException
from .devices import alarm as ALARM
from .helpers import urls
from .helpers import errors as ERROR
from .devices.base import Device
from . import settings
from . import config


log = logging.getLogger(__name__)


@retry(
    retries=1,
    cleanup=lambda: config.paths.user_data.joinpath('cookies.json').unlink(),
    trap=Exception,
)
def _cookies():
    return cookies.ShelvedCookieJar.create(config.paths.user_data)


class Client:
    """Client to an Abode system."""

    def __init__(
        self,
        username=None,
        password=None,
        auto_login=False,
        get_devices=False,
        get_automations=False,
    ):
        self._session = None
        self._token = None
        self._panel = None
        self._user = None
        self._username = username
        self._password = password

        self._event_controller = EventController(self)

        self._default_alarm_mode = 'away'

        self._devices = None

        self._automations = None

        self._session = sessions.BaseUrlSession(urls.BASE)
        self._session.cookies = _cookies()

        if auto_login:
            self.login()

        if get_devices:
            self.get_devices()

        if get_automations:
            self.get_automations()

    def login(self, username=None, password=None, mfa_code=None):
        """Explicit Abode login."""

        self._token = None

        username = username or self._username
        password = password or self._password

        if not isinstance(username, str):
            raise AuthenticationException(ERROR.USERNAME)

        if not isinstance(password, str):
            raise AuthenticationException(ERROR.PASSWORD)

        login_data = {
            'id': username,
            'password': password,
            'uuid': self._session.cookies.get('uuid') or str(uuid.uuid1()),
        }

        if mfa_code is not None:
            login_data['mfa_code'] = mfa_code
            login_data['remember_me'] = 1

        response = self._session.post(urls.LOGIN, json=login_data)
        AuthenticationException.raise_for(response)
        response_object = response.json()

        # Check for multi-factor authentication
        if 'mfa_type' in response_object:
            if response_object['mfa_type'] == "google_authenticator":
                raise AuthenticationException(ERROR.MFA_CODE_REQUIRED)

            raise AuthenticationException(ERROR.UNKNOWN_MFA_TYPE)

        oauth_response = self._session.get(urls.OAUTH_TOKEN)
        AuthenticationException.raise_for(oauth_response)
        oauth_response_object = oauth_response.json()

        log.debug("Login Response: %s", response.text)

        self._token = response_object['token']
        self._panel = response_object['panel']
        self._user = response_object['user']
        self._oauth_token = oauth_response_object['access_token']

        log.info("Login successful")

    def logout(self):
        """Explicit Abode logout."""
        if not self._token:
            return

        header_data = {'ABODE-API-KEY': self._token}

        self._session = sessions.BaseUrlSession(urls.BASE)
        self._token = None
        self._panel = None
        self._user = None
        self._devices = None
        self._automations = None

        try:
            response = self._session.post(urls.LOGOUT, headers=header_data)
        except OSError as exc:
            log.warning("Caught exception during logout: %s", exc)
            return

        AuthenticationException.raise_for(response)

        log.debug("Logout Response: %s", response.text)

        log.info("Logout successful")

    def refresh(self):
        """Do a full refresh of all devices and automations."""
        self.get_devices(refresh=True)
        self.get_automations(refresh=True)

    def get_devices(self, refresh=False, generic_type=None):
        """Get all devices from Abode."""
        if refresh or self._devices is None:
            self._load_devices()

        spec_types = (
            Everything() if generic_type is None else set(always_iterable(generic_type))
        )

        return [
            device
            for device in self._devices.values()
            if device.generic_type in spec_types
        ]

    def _load_devices(self):
        if self._devices is None:
            self._devices = {}

        log.info("Updating all devices...")
        response = self.send_request("get", urls.DEVICES)
        devices = always_iterable(response.json())

        log.debug("Get Devices Response: %s", response.text)

        consume(map(self._load_device, devices))

        # We will be treating the Abode panel itself as an armable device.
        panel_response = self.send_request("get", urls.PANEL)
        panel_json = panel_response.json()

        self._panel.update(panel_json)

        log.debug("Get Mode Panel Response: %s", response.text)

        alarm_device = self._devices.get(ALARM.id(1))

        if alarm_device:
            alarm_device.update(self._panel)
        else:
            alarm_device = ALARM.create_alarm(self._panel, self)
            self._devices[alarm_device.id] = alarm_device

    def _load_device(self, doc):
        self._reuse_device(doc) or self._create_new_device(doc)

    def _reuse_device(self, doc):
        device = self._devices.get(doc['id'])

        if not device:
            return

        device.update(doc)
        return device

    def _create_new_device(self, doc):
        device = Device.new(doc, self)

        if not device:
            log.debug("Skipping unknown device: %s", doc)
            return

        self._devices[device.id] = device

    def get_device(self, device_id, refresh=False):
        """Get a single device."""
        if self._devices is None:
            self.get_devices()
            refresh = False

        device = self._devices.get(device_id)

        if device and refresh:
            device.refresh()

        return device

    def get_automations(self, refresh=False):
        """Get all automations."""
        if refresh or self._automations is None:
            self._update_all()

        return list(self._automations.values())

    def _update_all(self):
        if self._automations is None:
            # Set up the device libraries
            self._automations = {}

        log.info("Updating all automations...")
        resp = self.send_request("get", urls.AUTOMATION)
        log.debug("Get Automations Response: %s", resp.text)

        for state in always_iterable(resp.json()):
            # Attempt to reuse an existing automation object
            automation = self._automations.get(str(state['id']))

            # No existing automation, create a new one
            if automation:
                automation.update(state)
            else:
                automation = Automation(state, self)
                self._automations[automation.id] = automation

    def get_automation(self, automation_id, refresh=False):
        """Get a single automation."""
        if self._automations is None:
            self.get_automations()
            refresh = False

        automation = self._automations.get(str(automation_id))

        if automation and refresh:
            automation.refresh()

        return automation

    def get_alarm(self, area='1', refresh=False):
        """Shortcut method to get the alarm device."""
        return self.get_device(ALARM.id(area), refresh)

    def set_default_mode(self, default_mode):
        """Set the default mode when alarms are turned 'on'."""
        if default_mode.lower() not in ('away', 'home'):
            raise jaraco.abode.Exception(ERROR.INVALID_DEFAULT_ALARM_MODE)

        self._default_alarm_mode = default_mode.lower()

    def set_setting(self, name, value, area='1'):
        """Set an abode system setting to a given value."""
        setting = settings.Setting.load(name.lower(), value, area)
        return self.send_request(method="put", path=setting.path, data=setting.data)

    def send_request(self, method, path, headers=None, data=None):
        """Send requests to Abode."""
        attempt = functools.partial(self._send_request, method, path, headers, data)
        return jaraco.functools.retry_call(
            attempt,
            retries=1,
            cleanup=self.login,
            trap=(jaraco.abode.Exception),
        )

    def _send_request(self, method, path, headers, data):
        if not self._token:
            self.login()

        if not headers:
            headers = {}

        headers['Authorization'] = 'Bearer ' + self._oauth_token
        headers['ABODE-API-KEY'] = self._token

        try:
            response = getattr(self._session, method)(path, headers=headers, json=data)

            if response and response.status_code < 400:
                return response
        except RequestException:
            log.info("Abode connection reset...")

        raise jaraco.abode.Exception(ERROR.REQUEST)

    @property
    def default_mode(self):
        """Get the default mode."""
        return self._default_alarm_mode

    @property
    def events(self):
        """Get the event controller."""
        return self._event_controller

    @property
    def uuid(self):
        """Get the UUID."""
        return self._session.cookies['uuid']

    def _get_session(self):
        # Perform a generic update so we know we're logged in
        self.send_request("get", urls.PANEL)

        return self._session
