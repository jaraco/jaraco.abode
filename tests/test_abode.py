"""
Test Abode system setup, shutdown, and general functionality.

Tests the system initialization and attributes of the main Abode system.
"""
import pytest
import requests

import jaraco.abode
import jaraco.abode.devices.status as STATUS
from jaraco.abode.helpers import urls
from jaraco.abode import settings
from jaraco.abode import config

from . import mock as MOCK
from .mock import login as LOGIN
from .mock import oauth_claims as OAUTH_CLAIMS
from .mock import logout as LOGOUT
from .mock import panel as PANEL
from .mock import devices as DEVICES
from .mock.devices import door_contact as DOOR_CONTACT
from .mock import user as USER


@pytest.fixture(autouse=True)
def abode_objects(request):
    self = request.instance
    self.client_no_cred = jaraco.abode.Client()


USERNAME = 'foobar'
PASSWORD = 'deadbeef'


class TestAbode:
    """Test the Abode class."""

    def test_initialization(self):
        """Verify we can initialize abode."""

        assert self.client._username == USERNAME

        assert self.client._password == PASSWORD

    def test_no_credentials(self):
        """Check that we throw an exception when no username/password."""
        with pytest.raises(jaraco.abode.AuthenticationException):
            self.client_no_cred.login()

        self.client_no_cred._username = USERNAME
        with pytest.raises(jaraco.abode.AuthenticationException):
            self.client_no_cred.login()

    def test_manual_login(self, m):
        """Check that we can manually use the login() function."""
        m.post(urls.LOGIN, json=LOGIN.post_response_ok())
        m.get(urls.OAUTH_TOKEN, json=OAUTH_CLAIMS.get_response_ok())

        self.client_no_cred.login(username=USERNAME, password=PASSWORD)

    def test_manual_login_with_mfa(self, m):
        """Check that we can login with MFA code."""
        m.post(urls.LOGIN, json=LOGIN.post_response_ok())
        m.get(urls.OAUTH_TOKEN, json=OAUTH_CLAIMS.get_response_ok())

        self.client_no_cred.login(username=USERNAME, password=PASSWORD, mfa_code=654321)

    def test_auto_login(self, m):
        """Test that automatic login works."""
        auth_token = MOCK.AUTH_TOKEN
        user_json = USER.get_response_ok()
        login_json = LOGIN.post_response_ok(auth_token, user_json)
        panel_json = PANEL.get_response_ok()

        m.post(urls.LOGIN, json=login_json)
        m.get(urls.OAUTH_TOKEN, json=OAUTH_CLAIMS.get_response_ok())
        m.get(urls.PANEL, json=panel_json)
        m.post(urls.LOGOUT, json=LOGOUT.post_response_ok())

        client = jaraco.abode.Client(
            username='fizz',
            password='buzz',
            auto_login=True,
            get_devices=False,
        )

        assert client._username == 'fizz'
        assert client._password == 'buzz'
        assert client._token == MOCK.AUTH_TOKEN
        assert client._panel == panel_json
        assert client._user == user_json
        assert client._devices is None
        assert client._automations is None

        client.logout()

        client = None

    def test_auto_fetch(self, m):
        """Test that automatic device and automation retrieval works."""
        auth_token = MOCK.AUTH_TOKEN
        user_json = USER.get_response_ok()
        login_json = LOGIN.post_response_ok(auth_token, user_json)
        panel_json = PANEL.get_response_ok()

        m.post(urls.LOGIN, json=login_json)
        m.get(urls.OAUTH_TOKEN, json=OAUTH_CLAIMS.get_response_ok())
        m.get(urls.PANEL, json=panel_json)
        m.get(urls.DEVICES, json=DEVICES.EMPTY_DEVICE_RESPONSE)
        m.get(urls.AUTOMATION, json=DEVICES.EMPTY_DEVICE_RESPONSE)
        m.post(urls.LOGOUT, json=LOGOUT.post_response_ok())

        client = jaraco.abode.Client(
            username='fizz',
            password='buzz',
            auto_login=False,
            get_devices=True,
            get_automations=True,
        )

        assert client._username == 'fizz'
        assert client._password == 'buzz'
        assert client._token == MOCK.AUTH_TOKEN
        assert client._user == user_json
        assert client._panel is not None

        # Contains one device, our alarm
        assert client._devices == {'area_1': client.get_alarm()}

        # Contains no automations
        assert client._automations == {}

        client.logout()

        client = None

    def test_login_failure(self, m):
        """Test login failed."""
        m.post(urls.LOGIN, json=LOGIN.post_response_bad_request(), status_code=400)
        m.get(urls.OAUTH_TOKEN, json=OAUTH_CLAIMS.get_response_ok())

        # Check that we raise an Exception with a failed login request.
        with pytest.raises(jaraco.abode.AuthenticationException):
            self.client_no_cred.login(username=USERNAME, password=PASSWORD)

    def test_login_mfa_required(self, m):
        """Tests login with MFA code required but not supplied."""
        m.post(
            urls.LOGIN,
            json=LOGIN.post_response_mfa_code_required(),
            status_code=200,
        )

        # Check that we raise an Exception when the MFA code is required
        # but not supplied
        with pytest.raises(jaraco.abode.AuthenticationException):
            self.client_no_cred.login(username=USERNAME, password=PASSWORD)

    def test_login_bad_mfa_code(self, m):
        """Tests login with bad MFA code."""
        m.post(urls.LOGIN, json=LOGIN.post_response_bad_mfa_code(), status_code=400)

        # Check that we raise an Exception with a bad MFA code
        with pytest.raises(jaraco.abode.AuthenticationException):
            self.client_no_cred.login(
                username=USERNAME, password=PASSWORD, mfa_code=123456
            )

    def test_login_unknown_mfa_type(self, m):
        """Tests login with unknown MFA type."""
        m.post(
            urls.LOGIN,
            json=LOGIN.post_response_unknown_mfa_type(),
            status_code=200,
        )

        # Check that we raise an Exception with an unknown MFA type
        with pytest.raises(jaraco.abode.AuthenticationException):
            self.client_no_cred.login(username=USERNAME, password=PASSWORD)

    def test_logout_failure(self, m):
        """Test logout failed."""
        m.post(urls.LOGIN, json=LOGIN.post_response_ok())
        m.get(urls.OAUTH_TOKEN, json=OAUTH_CLAIMS.get_response_ok())
        m.get(urls.DEVICES, json=DEVICES.EMPTY_DEVICE_RESPONSE)
        m.get(urls.PANEL, json=PANEL.get_response_ok())
        m.post(urls.LOGOUT, json=LOGOUT.post_response_bad_request(), status_code=400)

        self.client_no_cred.login(username=USERNAME, password=PASSWORD)

        # Check that we raise an Exception with a failed logout request.
        with pytest.raises(jaraco.abode.AuthenticationException):
            self.client_no_cred.logout()

    def test_logout_exception(self, m):
        """Test logout exception."""
        m.post(urls.LOGIN, json=LOGIN.post_response_ok())
        m.get(urls.OAUTH_TOKEN, json=OAUTH_CLAIMS.get_response_ok())
        m.get(urls.DEVICES, json=DEVICES.EMPTY_DEVICE_RESPONSE)
        m.get(urls.PANEL, json=PANEL.get_response_ok())
        m.post(urls.LOGOUT, exc=requests.exceptions.ConnectTimeout)

        self.client.login()

        # Check that we eat the exception gracefully
        assert not self.client.logout()

    def test_full_setup(self, m):
        """Check that Abode is set up properly."""
        auth_token = MOCK.AUTH_TOKEN
        user_json = USER.get_response_ok()
        login_json = LOGIN.post_response_ok(auth_token, user_json)
        panel_json = PANEL.get_response_ok()

        m.post(urls.LOGIN, json=login_json)
        m.get(urls.OAUTH_TOKEN, json=OAUTH_CLAIMS.get_response_ok())
        m.get(urls.PANEL, json=panel_json)
        m.get(urls.DEVICES, json=DEVICES.EMPTY_DEVICE_RESPONSE)
        m.post(urls.LOGOUT, json=LOGOUT.post_response_ok())

        self.client.get_devices()

        original_session = self.client._session

        assert self.client._username == USERNAME
        assert self.client._password == PASSWORD
        assert self.client._token == auth_token
        assert self.client._user == user_json
        assert self.client._panel is not None
        assert self.client.get_alarm() is not None
        assert self.client._get_session() is not None
        assert self.client._get_session() == original_session
        assert self.client.events is not None

        self.client.logout()

        assert self.client._token is None
        assert self.client._panel is None
        assert self.client._user is None
        assert self.client._devices is None
        assert self.client._automations is None
        assert self.client._session is not None
        assert self.client._get_session() != original_session

    def test_reauthorize(self, m):
        """Check that Abode can reauthorize after token timeout."""
        new_token = "FOOBAR"
        m.post(
            urls.LOGIN,
            [
                dict(
                    json=LOGIN.post_response_ok(auth_token=new_token),
                    status_code=200,
                ),
            ],
        )

        m.get(urls.OAUTH_TOKEN, json=OAUTH_CLAIMS.get_response_ok())

        m.get(
            urls.DEVICES,
            [
                dict(json=MOCK.response_forbidden(), status_code=403),
                dict(json=DEVICES.EMPTY_DEVICE_RESPONSE, status_code=200),
            ],
        )
        m.get(urls.PANEL, json=PANEL.get_response_ok())

        # Forces a device update
        self.client.get_devices()

        assert self.client._token == new_token

    def test_send_request_exception(self, m):
        """Check that send_request recovers from an exception."""
        new_token = "DEADBEEF"
        m.post(
            urls.LOGIN,
            [
                dict(
                    json=LOGIN.post_response_ok(auth_token=new_token),
                    status_code=200,
                )
            ],
        )

        m.get(urls.OAUTH_TOKEN, json=OAUTH_CLAIMS.get_response_ok())

        m.get(
            urls.DEVICES,
            [
                dict(exc=requests.exceptions.ConnectTimeout),
                dict(json=DEVICES.EMPTY_DEVICE_RESPONSE, status_code=200),
            ],
        )
        m.get(urls.PANEL, json=PANEL.get_response_ok())

        # Forces a device update
        self.client.get_devices()

        assert self.client._token == new_token

    def test_continuous_bad_auth(self, m):
        """Check that Abode won't get stuck with repeated failed retries."""
        m.post(urls.LOGIN, json=LOGIN.post_response_ok())
        m.get(urls.OAUTH_TOKEN, json=OAUTH_CLAIMS.get_response_ok())
        m.get(urls.DEVICES, json=MOCK.response_forbidden(), status_code=403)

        with pytest.raises(jaraco.abode.Exception):
            self.client.get_devices()

    def test_default_mode(self):
        """Test that the default mode fails if not of type home or away."""
        self.client.set_default_mode('home')
        assert self.client.default_mode == 'home'

        self.client.set_default_mode('away')
        assert self.client.default_mode == 'away'

        with pytest.raises(jaraco.abode.Exception):
            self.client.set_default_mode('foobar')

    def test_all_device_refresh(self, m):
        """Check that device refresh works and reuses the same objects."""
        dc1_devid = 'RF:01'
        dc1a = DOOR_CONTACT.device(devid=dc1_devid, status=STATUS.ON)

        dc2_devid = 'RF:02'
        dc2a = DOOR_CONTACT.device(devid=dc2_devid, status=STATUS.OFF)

        m.post(urls.LOGIN, json=LOGIN.post_response_ok())
        m.get(urls.OAUTH_TOKEN, json=OAUTH_CLAIMS.get_response_ok())
        m.post(urls.LOGOUT, json=LOGOUT.post_response_ok())
        m.get(urls.DEVICES, json=[dc1a, dc2a])
        m.get(urls.PANEL, json=PANEL.get_response_ok())

        # Reset
        self.client.logout()

        # Get all devices
        self.client.get_devices()

        # Get and check devices

        dc1a_dev = self.client.get_device(dc1_devid)
        assert dc1a['id'] == dc1a_dev.id

        dc2a_dev = self.client.get_device(dc2_devid)
        assert dc2a['id'] == dc2a_dev.id

        # Change device states
        dc1b = DOOR_CONTACT.device(devid=dc1_devid, status=STATUS.OFF)

        dc2b = DOOR_CONTACT.device(devid=dc2_devid, status=STATUS.ON)

        m.get(urls.DEVICES, json=[dc1b, dc2b])

        # Refresh all devices
        self.client.get_devices(refresh=True)

        # Get and check devices again, ensuring they are the same object
        # Future note: "if a is b" tests that the object is the same
        # Thus asserting dc1a_dev is dc1b_dev tests if they are the same object
        dc1b_dev = self.client.get_device(dc1_devid)
        assert dc1b['id'] == dc1b_dev.id
        assert dc1a_dev is dc1b_dev

        dc2b_dev = self.client.get_device(dc2_devid)
        assert dc2b['id'] == dc2b_dev.id
        assert dc2a_dev is dc2b_dev

    def test_settings_validation(self, m):
        """Check that device panel general settings are working."""
        m.post(urls.LOGIN, json=LOGIN.post_response_ok())
        m.get(urls.OAUTH_TOKEN, json=OAUTH_CLAIMS.get_response_ok())
        m.post(urls.LOGOUT, json=LOGOUT.post_response_ok())
        m.get(urls.PANEL, json=PANEL.get_response_ok())
        m.get(urls.SETTINGS, json=MOCK.generic_response_ok())

        with pytest.raises(jaraco.abode.Exception):
            self.client.set_setting("fliptrix", "foobar")

    def test_general_settings(self, m):
        """Check that device panel general settings are working."""
        m.post(urls.LOGIN, json=LOGIN.post_response_ok())
        m.get(urls.OAUTH_TOKEN, json=OAUTH_CLAIMS.get_response_ok())
        m.post(urls.LOGOUT, json=LOGOUT.post_response_ok())
        m.get(urls.PANEL, json=PANEL.get_response_ok())
        m.put(urls.SETTINGS, json=MOCK.generic_response_ok())

        self.client.set_setting(settings.CAMERA_RESOLUTION, settings.CAMERA_RES_640_480)

        self.client.set_setting(settings.CAMERA_GRAYSCALE, settings.ENABLE)

        self.client.set_setting(settings.SILENCE_SOUNDS, settings.ENABLE)

        with pytest.raises(jaraco.abode.Exception):
            self.client.set_setting(settings.CAMERA_RESOLUTION, "foobar")

        with pytest.raises(jaraco.abode.Exception):
            self.client.set_setting(settings.CAMERA_GRAYSCALE, "foobar")

        with pytest.raises(jaraco.abode.Exception):
            self.client.set_setting(settings.SILENCE_SOUNDS, "foobar")

    def test_area_settings(self, m):
        """Check that device panel areas settings are working."""
        m.post(urls.LOGIN, json=LOGIN.post_response_ok())
        m.get(urls.OAUTH_TOKEN, json=OAUTH_CLAIMS.get_response_ok())
        m.post(urls.LOGOUT, json=LOGOUT.post_response_ok())
        m.get(urls.PANEL, json=PANEL.get_response_ok())
        m.put(urls.AREAS, json=MOCK.generic_response_ok())

        self.client.set_setting(
            settings.ENTRY_DELAY_AWAY, settings.ENTRY_EXIT_DELAY_10SEC
        )

        self.client.set_setting(
            settings.EXIT_DELAY_AWAY, settings.ENTRY_EXIT_DELAY_30SEC
        )

        with pytest.raises(jaraco.abode.Exception):
            self.client.set_setting(settings.ENTRY_DELAY_AWAY, "foobar")

        # 10 seconds is invalid here
        with pytest.raises(jaraco.abode.Exception):
            self.client.set_setting(
                settings.EXIT_DELAY_AWAY, settings.ENTRY_EXIT_DELAY_10SEC
            )

    def test_sound_settings(self, m):
        """Check that device panel sound settings are working."""
        m.post(urls.LOGIN, json=LOGIN.post_response_ok())
        m.get(urls.OAUTH_TOKEN, json=OAUTH_CLAIMS.get_response_ok())
        m.post(urls.LOGOUT, json=LOGOUT.post_response_ok())
        m.get(urls.PANEL, json=PANEL.get_response_ok())
        m.put(urls.SOUNDS, json=MOCK.generic_response_ok())

        self.client.set_setting(settings.DOOR_CHIME, settings.SOUND_LOW)

        self.client.set_setting(settings.ALARM_LENGTH, settings.ALARM_LENGTH_2MIN)

        self.client.set_setting(settings.FINAL_BEEPS, settings.FINAL_BEEPS_3SEC)

        with pytest.raises(jaraco.abode.Exception):
            self.client.set_setting(settings.DOOR_CHIME, "foobar")

        with pytest.raises(jaraco.abode.Exception):
            self.client.set_setting(settings.ALARM_LENGTH, "foobar")

        with pytest.raises(jaraco.abode.Exception):
            self.client.set_setting(settings.FINAL_BEEPS, "foobar")

    def test_siren_settings(self, m):
        """Check that device panel siren settings are working."""
        m.post(urls.LOGIN, json=LOGIN.post_response_ok())
        m.get(urls.OAUTH_TOKEN, json=OAUTH_CLAIMS.get_response_ok())
        m.post(urls.LOGOUT, json=LOGOUT.post_response_ok())
        m.get(urls.PANEL, json=PANEL.get_response_ok())
        m.put(urls.SIREN, json=MOCK.generic_response_ok())

        self.client.set_setting(settings.SIREN_ENTRY_EXIT_SOUNDS, settings.ENABLE)

        self.client.set_setting(settings.SIREN_CONFIRM_SOUNDS, settings.ENABLE)

        self.client.set_setting(settings.SIREN_TAMPER_SOUNDS, settings.ENABLE)

        with pytest.raises(jaraco.abode.Exception):
            self.client.set_setting(settings.SIREN_ENTRY_EXIT_SOUNDS, "foobar")

        with pytest.raises(jaraco.abode.Exception):
            self.client.set_setting(settings.SIREN_CONFIRM_SOUNDS, "foobar")

        with pytest.raises(jaraco.abode.Exception):
            self.client.set_setting(settings.SIREN_TAMPER_SOUNDS, "foobar")

    def test_cookies(self, m):
        """Check that cookies are saved and loaded successfully."""
        cookies = dict(SESSION='COOKIE')
        m.post(urls.LOGIN, json=LOGIN.post_response_ok(), cookies=cookies)
        m.get(urls.OAUTH_TOKEN, json=OAUTH_CLAIMS.get_response_ok())
        m.post(urls.LOGOUT, json=LOGOUT.post_response_ok())
        m.get(urls.DEVICES, json=DEVICES.EMPTY_DEVICE_RESPONSE)
        m.get(urls.PANEL, json=PANEL.get_response_ok())

        # Create abode
        client = jaraco.abode.Client(
            username='fizz',
            password='buzz',
            auto_login=False,
            get_devices=False,
        )

        client.login()

        # Test that our cookies are fully realized prior to login

        assert client._session.cookies

        # Test that we now have a cookies file
        cookies_file = config.paths.user_data / 'cookies.json'
        assert cookies_file.exists()

        # Copy the current cookies
        saved_cookies = client._session.cookies

        # New client reads in old data
        client = jaraco.abode.Client(
            username='fizz',
            password='buzz',
            auto_login=False,
            get_devices=False,
        )

        # Test that the cookie data is the same
        assert str(client._session.cookies) == str(saved_cookies)

    def test_empty_cookies(self, m):
        """Check that empty cookies file is loaded successfully."""
        cookies = dict(SESSION='COOKIE')
        m.post(urls.LOGIN, json=LOGIN.post_response_ok(), cookies=cookies)
        m.get(urls.OAUTH_TOKEN, json=OAUTH_CLAIMS.get_response_ok())
        m.post(urls.LOGOUT, json=LOGOUT.post_response_ok())
        m.get(urls.DEVICES, json=DEVICES.EMPTY_DEVICE_RESPONSE)
        m.get(urls.PANEL, json=PANEL.get_response_ok())

        # Create an empty file
        cookie_file = config.paths.user_data / 'cookies.json'

        # Cookies are created
        jaraco.abode.Client(
            username='fizz',
            password='buzz',
            auto_login=True,
            get_devices=False,
        )

        # Test that some cookie data exists
        assert cookie_file.read_bytes()

    def test_invalid_cookies(self, m):
        """Check that empty cookies file is loaded successfully."""
        cookies = dict(SESSION='COOKIE')
        m.post(urls.LOGIN, json=LOGIN.post_response_ok(), cookies=cookies)
        m.get(urls.OAUTH_TOKEN, json=OAUTH_CLAIMS.get_response_ok())
        m.post(urls.LOGOUT, json=LOGOUT.post_response_ok())
        m.get(urls.DEVICES, json=DEVICES.EMPTY_DEVICE_RESPONSE)
        m.get(urls.PANEL, json=PANEL.get_response_ok())

        # Create an invalid pickle file
        config.paths.user_data.joinpath('cookies.json').write_text(
            'invalid cookies', encoding='utf-8'
        )

        # Cookies are created
        empty_client = jaraco.abode.Client(
            username='fizz',
            password='buzz',
            auto_login=True,
            get_devices=False,
        )

        # Test that some cache exists
        assert empty_client._session.cookies
