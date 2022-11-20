"""
An Abode alarm Python library.
"""

import logging
import os
import uuid

from more_itertools import always_iterable
from requests_toolbelt import sessions
from requests.exceptions import RequestException

import jaraco
from .automation import Automation
from .event_controller import EventController
from .exceptions import AuthenticationException
from .devices import alarm as ALARM
from .helpers import urls
from .helpers import constants as CONST
from .helpers import errors as ERROR
from . import collections as COLLECTIONS
from . import cache as CACHE
from .devices.base import Device
from . import settings


_LOGGER = logging.getLogger(__name__)


class Client:
    """Client to an Abode system."""

    def __init__(
        self,
        username=None,
        password=None,
        auto_login=False,
        get_devices=False,
        get_automations=False,
        cache_path=CONST.CACHE_PATH,
        disable_cache=False,
    ):
        """Init Abode object."""
        self._session = None
        self._token = None
        self._panel = None
        self._user = None
        self._cache_path = cache_path
        self._disable_cache = disable_cache
        self._username = username
        self._password = password

        self._event_controller = EventController(self, url=CONST.SOCKETIO_URL)

        self._default_alarm_mode = CONST.MODE_AWAY

        self._devices = None

        self._automations = None

        # Create a requests session to persist the cookies
        self._session = sessions.BaseUrlSession(urls.BASE)

        # Create a new cache template
        self._cache = {
            CONST.UUID: str(uuid.uuid1()),
            CONST.COOKIES: None,
        }

        # Load and merge an existing cache
        if not disable_cache:
            self._load_cache()

        # Load persisted cookies (which contains the UUID and the session ID)
        # if available
        if CONST.COOKIES in self._cache and self._cache[CONST.COOKIES] is not None:
            self._session.cookies = self._cache[CONST.COOKIES]

        if auto_login:
            self.login()

        if get_devices:
            self.get_devices()

        if get_automations:
            self.get_automations()

    def login(self, username=None, password=None, mfa_code=None):  # noqa: C901
        """Explicit Abode login."""

        self._token = None

        username = username or self._username
        password = password or self._password

        if not isinstance(username, str):
            raise AuthenticationException(ERROR.USERNAME)

        if not isinstance(password, str):
            raise AuthenticationException(ERROR.PASSWORD)

        login_data = {
            CONST.ID: username,
            CONST.PASSWORD: password,
            CONST.UUID: self._cache[CONST.UUID],
        }

        if mfa_code is not None:
            login_data[CONST.MFA_CODE] = mfa_code
            login_data['remember_me'] = 1

        response = self._session.post(urls.LOGIN, json=login_data)
        AuthenticationException.raise_for(response)
        response_object = response.json()

        # Check for multi-factor authentication
        if 'mfa_type' in response_object:
            if response_object['mfa_type'] == "google_authenticator":
                raise AuthenticationException(ERROR.MFA_CODE_REQUIRED)

            raise AuthenticationException(ERROR.UNKNOWN_MFA_TYPE)

        # Persist cookies (which contains the UUID and the session ID) to disk
        if self._session.cookies.get_dict():
            self._cache[CONST.COOKIES] = self._session.cookies
            self._save_cache()

        oauth_response = self._session.get(urls.OAUTH_TOKEN)
        AuthenticationException.raise_for(oauth_response)
        oauth_response_object = oauth_response.json()

        _LOGGER.debug("Login Response: %s", response.text)

        self._token = response_object['token']
        self._panel = response_object['panel']
        self._user = response_object['user']
        self._oauth_token = oauth_response_object['access_token']

        _LOGGER.info("Login successful")

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
            _LOGGER.warning("Caught exception during logout: %s", exc)
            return

        AuthenticationException.raise_for(response)

        _LOGGER.debug("Logout Response: %s", response.text)

        _LOGGER.info("Logout successful")

    def refresh(self):
        """Do a full refresh of all devices and automations."""
        self.get_devices(refresh=True)
        self.get_automations(refresh=True)

    def get_devices(self, refresh=False, generic_type=None):
        """Get all devices from Abode."""
        if refresh or self._devices is None:
            self._load_devices()

        return [
            device
            for device in self._devices.values()
            if not generic_type or device.generic_type == generic_type
        ]

    def _load_devices(self):
        if self._devices is None:
            self._devices = {}

        _LOGGER.info("Updating all devices...")
        response = self.send_request("get", urls.DEVICES)
        response_object = response.json()

        if response_object and not isinstance(response_object, (tuple, list)):
            response_object = [response_object]

        _LOGGER.debug("Get Devices Response: %s", response.text)

        for device_json in response_object:
            # Attempt to reuse an existing device
            device = self._devices.get(device_json['id'])

            # No existing device, create a new one
            if device:
                device.update(device_json)
            else:
                device = Device.new(device_json, self)

                if not device:
                    _LOGGER.debug("Skipping unknown device: %s", device_json)

                    continue

                self._devices[device.device_id] = device

        # We will be treating the Abode panel itself as an armable device.
        panel_response = self.send_request("get", urls.PANEL)
        panel_json = panel_response.json()

        self._panel.update(panel_json)

        _LOGGER.debug("Get Mode Panel Response: %s", response.text)

        alarm_device = self._devices.get(CONST.ALARM_DEVICE_ID + '1')

        if alarm_device:
            alarm_device.update(self._panel)
        else:
            alarm_device = ALARM.create_alarm(self._panel, self)
            self._devices[alarm_device.device_id] = alarm_device

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
            if self._automations is None:
                # Set up the device libraries
                self._automations = {}

            _LOGGER.info("Updating all automations...")
            resp = self.send_request("get", urls.AUTOMATION)
            _LOGGER.debug("Get Automations Response: %s", resp.text)

            for automation_ob in always_iterable(resp.json(), base_type=dict):
                # Attempt to reuse an existing automation object
                automation = self._automations.get(str(automation_ob['id']))

                # No existing automation, create a new one
                if automation:
                    automation.update(automation_ob)
                else:
                    automation = Automation(self, automation_ob)
                    self._automations[automation.automation_id] = automation

        return list(self._automations.values())

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
        return self.get_device(CONST.ALARM_DEVICE_ID + area, refresh)

    def set_default_mode(self, default_mode):
        """Set the default mode when alarms are turned 'on'."""
        if default_mode.lower() not in (CONST.MODE_AWAY, CONST.MODE_HOME):
            raise jaraco.abode.Exception(ERROR.INVALID_DEFAULT_ALARM_MODE)

        self._default_alarm_mode = default_mode.lower()

    def set_setting(self, name, value, area='1'):
        """Set an abode system setting to a given value."""
        setting = settings.Setting.load(name.lower(), value, area)
        return self.send_request(method="put", path=setting.path, data=setting.data)

    def send_request(self, method, path, headers=None, data=None, is_retry=False):
        """Send requests to Abode."""
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
            _LOGGER.info("Abode connection reset...")

        if not is_retry:
            # Delete our current token and try again -- will force a login
            # attempt.
            self._token = None

            return self.send_request(method, path, headers, data, True)

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
        return self._cache[CONST.UUID]

    def _get_session(self):
        # Perform a generic update so we know we're logged in
        self.send_request("get", urls.PANEL)

        return self._session

    def _load_cache(self):
        """Load existing cache and merge for updating if required."""
        if not self._disable_cache and os.path.exists(self._cache_path):
            _LOGGER.debug("Cache found at: %s", self._cache_path)
            loaded_cache = CACHE.load_cache(self._cache_path)

            if loaded_cache:
                COLLECTIONS.update(self._cache, loaded_cache)
            else:
                _LOGGER.debug("Removing invalid cache file: %s", self._cache_path)
                os.remove(self._cache_path)

        self._save_cache()

    def _save_cache(self):
        """Trigger a cache save."""
        if not self._disable_cache:
            CACHE.save_cache(self._cache, self._cache_path)
