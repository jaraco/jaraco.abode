"""
Test Abode system setup, shutdown, and general functionality.

Tests the system initialization and attributes of the main Abode system.
"""
import os
import json

import pytest
import requests

import jaraco.abode
import jaraco.abode.helpers.constants as CONST

from . import mock as MOCK
from .mock import login as LOGIN
from .mock import oauth_claims as OAUTH_CLAIMS
from .mock import logout as LOGOUT
from .mock import panel as PANEL
from .mock import devices as DEVICES
from .mock.devices import door_contact as DOOR_CONTACT
from .mock import user as USER


@pytest.fixture
def cache_path(tmp_path, request):
    request.instance.cache_path = tmp_path / 'cache.pickle'


@pytest.fixture(autouse=True)
def abode_objects(request):
    self = request.instance
    self.abode_no_cred = jaraco.abode.Abode(disable_cache=True)


USERNAME = 'foobar'
PASSWORD = 'deadbeef'


class TestAbode:
    """Test the Abode class."""

    def tests_initialization(self):
        """Verify we can initialize abode."""

        assert self.abode._username == USERNAME

        assert self.abode._password == PASSWORD

    def tests_no_credentials(self):
        """Check that we throw an exception when no username/password."""
        with pytest.raises(jaraco.abode.AbodeAuthenticationException):
            self.abode_no_cred.login()

        self.abode_no_cred._username = USERNAME
        with pytest.raises(jaraco.abode.AbodeAuthenticationException):
            self.abode_no_cred.login()

    def tests_manual_login(self, m):
        """Check that we can manually use the login() function."""
        m.post(CONST.LOGIN_URL, text=LOGIN.post_response_ok())
        m.get(CONST.OAUTH_TOKEN_URL, text=OAUTH_CLAIMS.get_response_ok())

        self.abode_no_cred.login(username=USERNAME, password=PASSWORD)

    def tests_manual_login_with_mfa(self, m):
        """Check that we can login with MFA code."""
        m.post(CONST.LOGIN_URL, text=LOGIN.post_response_ok())
        m.get(CONST.OAUTH_TOKEN_URL, text=OAUTH_CLAIMS.get_response_ok())

        self.abode_no_cred.login(username=USERNAME, password=PASSWORD, mfa_code=654321)

    def tests_auto_login(self, m):
        """Test that automatic login works."""
        auth_token = MOCK.AUTH_TOKEN
        user_json = USER.get_response_ok()
        login_json = LOGIN.post_response_ok(auth_token, user_json)
        panel_json = PANEL.get_response_ok()

        m.post(CONST.LOGIN_URL, text=login_json)
        m.get(CONST.OAUTH_TOKEN_URL, text=OAUTH_CLAIMS.get_response_ok())
        m.get(CONST.PANEL_URL, text=panel_json)
        m.post(CONST.LOGOUT_URL, text=LOGOUT.post_response_ok())

        abode = jaraco.abode.Abode(
            username='fizz',
            password='buzz',
            auto_login=True,
            get_devices=False,
            disable_cache=True,
        )

        assert abode._username == 'fizz'
        assert abode._password == 'buzz'
        assert abode._token == MOCK.AUTH_TOKEN
        assert abode._panel == json.loads(panel_json)
        assert abode._user == json.loads(user_json)
        assert abode._devices is None
        assert abode._automations is None

        abode.logout()

        abode = None

    def tests_auto_fetch(self, m):
        """Test that automatic device and automation retrieval works."""
        auth_token = MOCK.AUTH_TOKEN
        user_json = USER.get_response_ok()
        login_json = LOGIN.post_response_ok(auth_token, user_json)
        panel_json = PANEL.get_response_ok()

        m.post(CONST.LOGIN_URL, text=login_json)
        m.get(CONST.OAUTH_TOKEN_URL, text=OAUTH_CLAIMS.get_response_ok())
        m.get(CONST.PANEL_URL, text=panel_json)
        m.get(CONST.DEVICES_URL, text=DEVICES.EMPTY_DEVICE_RESPONSE)
        m.get(CONST.AUTOMATION_URL, text=DEVICES.EMPTY_DEVICE_RESPONSE)
        m.post(CONST.LOGOUT_URL, text=LOGOUT.post_response_ok())

        abode = jaraco.abode.Abode(
            username='fizz',
            password='buzz',
            auto_login=False,
            get_devices=True,
            get_automations=True,
            disable_cache=True,
        )

        assert abode._username == 'fizz'
        assert abode._password == 'buzz'
        assert abode._token == MOCK.AUTH_TOKEN
        assert abode._user == json.loads(user_json)
        assert abode._panel is not None

        # Contains one device, our alarm
        assert abode._devices == {'area_1': abode.get_alarm()}

        # Contains no automations
        assert abode._automations == {}

        abode.logout()

        abode = None

    def tests_login_failure(self, m):
        """Test login failed."""
        m.post(CONST.LOGIN_URL, text=LOGIN.post_response_bad_request(), status_code=400)
        m.get(CONST.OAUTH_TOKEN_URL, text=OAUTH_CLAIMS.get_response_ok())

        # Check that we raise an Exception with a failed login request.
        with pytest.raises(jaraco.abode.AbodeAuthenticationException):
            self.abode_no_cred.login(username=USERNAME, password=PASSWORD)

    def tests_login_mfa_required(self, m):
        """Tests login with MFA code required but not supplied."""
        m.post(
            CONST.LOGIN_URL,
            text=LOGIN.post_response_mfa_code_required(),
            status_code=200,
        )

        # Check that we raise an Exception when the MFA code is required
        # but not supplied
        with pytest.raises(jaraco.abode.AbodeAuthenticationException):
            self.abode_no_cred.login(username=USERNAME, password=PASSWORD)

    def tests_login_bad_mfa_code(self, m):
        """Tests login with bad MFA code."""
        m.post(
            CONST.LOGIN_URL, text=LOGIN.post_response_bad_mfa_code(), status_code=400
        )

        # Check that we raise an Exception with a bad MFA code
        with pytest.raises(jaraco.abode.AbodeAuthenticationException):
            self.abode_no_cred.login(
                username=USERNAME, password=PASSWORD, mfa_code=123456
            )

    def tests_login_unknown_mfa_type(self, m):
        """Tests login with unknown MFA type."""
        m.post(
            CONST.LOGIN_URL,
            text=LOGIN.post_response_unknown_mfa_type(),
            status_code=200,
        )

        # Check that we raise an Exception with an unknown MFA type
        with pytest.raises(jaraco.abode.AbodeAuthenticationException):
            self.abode_no_cred.login(username=USERNAME, password=PASSWORD)

    def tests_logout_failure(self, m):
        """Test logout failed."""
        m.post(CONST.LOGIN_URL, text=LOGIN.post_response_ok())
        m.get(CONST.OAUTH_TOKEN_URL, text=OAUTH_CLAIMS.get_response_ok())
        m.get(CONST.DEVICES_URL, text=DEVICES.EMPTY_DEVICE_RESPONSE)
        m.get(CONST.PANEL_URL, text=PANEL.get_response_ok())
        m.post(
            CONST.LOGOUT_URL, text=LOGOUT.post_response_bad_request(), status_code=400
        )

        self.abode_no_cred.login(username=USERNAME, password=PASSWORD)

        # Check that we raise an Exception with a failed logout request.
        with pytest.raises(jaraco.abode.AbodeAuthenticationException):
            self.abode_no_cred.logout()

    def tests_logout_exception(self, m):
        """Test logout exception."""
        m.post(CONST.LOGIN_URL, text=LOGIN.post_response_ok())
        m.get(CONST.OAUTH_TOKEN_URL, text=OAUTH_CLAIMS.get_response_ok())
        m.get(CONST.DEVICES_URL, text=DEVICES.EMPTY_DEVICE_RESPONSE)
        m.get(CONST.PANEL_URL, text=PANEL.get_response_ok())
        m.post(CONST.LOGOUT_URL, exc=requests.exceptions.ConnectTimeout)

        self.abode.login()

        # Check that we eat the exception gracefully
        assert not self.abode.logout()

    def tests_full_setup(self, m):
        """Check that Abode is set up properly."""
        auth_token = MOCK.AUTH_TOKEN
        user_json = USER.get_response_ok()
        login_json = LOGIN.post_response_ok(auth_token, user_json)
        panel_json = PANEL.get_response_ok()

        m.post(CONST.LOGIN_URL, text=login_json)
        m.get(CONST.OAUTH_TOKEN_URL, text=OAUTH_CLAIMS.get_response_ok())
        m.get(CONST.PANEL_URL, text=panel_json)
        m.get(CONST.DEVICES_URL, text=DEVICES.EMPTY_DEVICE_RESPONSE)
        m.post(CONST.LOGOUT_URL, text=LOGOUT.post_response_ok())

        self.abode.get_devices()

        original_session = self.abode._session

        assert self.abode._username == USERNAME
        assert self.abode._password == PASSWORD
        assert self.abode._token == auth_token
        assert self.abode._user == json.loads(user_json)
        assert self.abode._panel is not None
        assert self.abode.get_alarm() is not None
        assert self.abode._get_session() is not None
        assert self.abode._get_session() == original_session
        assert self.abode.events is not None

        self.abode.logout()

        assert self.abode._token is None
        assert self.abode._panel is None
        assert self.abode._user is None
        assert self.abode._devices is None
        assert self.abode._automations is None
        assert self.abode._session is not None
        assert self.abode._get_session() != original_session

    def tests_reauthorize(self, m):
        """Check that Abode can reauthorize after token timeout."""
        new_token = "FOOBAR"
        m.post(
            CONST.LOGIN_URL,
            [
                {
                    'text': LOGIN.post_response_ok(auth_token=new_token),
                    'status_code': 200,
                }
            ],
        )

        m.get(CONST.OAUTH_TOKEN_URL, text=OAUTH_CLAIMS.get_response_ok())

        m.get(
            CONST.DEVICES_URL,
            [
                {'text': MOCK.response_forbidden(), 'status_code': 403},
                {'text': DEVICES.EMPTY_DEVICE_RESPONSE, 'status_code': 200},
            ],
        )
        m.get(CONST.PANEL_URL, text=PANEL.get_response_ok())

        # Forces a device update
        self.abode.get_devices()

        assert self.abode._token == new_token

    def tests_send_request_exception(self, m):
        """Check that send_request recovers from an exception."""
        new_token = "DEADBEEF"
        m.post(
            CONST.LOGIN_URL,
            [
                {
                    'text': LOGIN.post_response_ok(auth_token=new_token),
                    'status_code': 200,
                }
            ],
        )

        m.get(CONST.OAUTH_TOKEN_URL, text=OAUTH_CLAIMS.get_response_ok())

        m.get(
            CONST.DEVICES_URL,
            [
                {'exc': requests.exceptions.ConnectTimeout},
                {'text': DEVICES.EMPTY_DEVICE_RESPONSE, 'status_code': 200},
            ],
        )
        m.get(CONST.PANEL_URL, text=PANEL.get_response_ok())

        # Forces a device update
        self.abode.get_devices()

        assert self.abode._token == new_token

    def tests_continuous_bad_auth(self, m):
        """Check that Abode won't get stuck with repeated failed retries."""
        m.post(CONST.LOGIN_URL, text=LOGIN.post_response_ok())
        m.get(CONST.OAUTH_TOKEN_URL, text=OAUTH_CLAIMS.get_response_ok())
        m.get(CONST.DEVICES_URL, text=MOCK.response_forbidden(), status_code=403)

        with pytest.raises(jaraco.abode.AbodeException):
            self.abode.get_devices()

    def tests_default_mode(self):
        """Test that the default mode fails if not of type home or away."""
        self.abode.set_default_mode(CONST.MODE_HOME)
        assert self.abode.default_mode == CONST.MODE_HOME

        self.abode.set_default_mode(CONST.MODE_AWAY)
        assert self.abode.default_mode == CONST.MODE_AWAY

        with pytest.raises(jaraco.abode.AbodeException):
            self.abode.set_default_mode('foobar')

    def test_all_device_refresh(self, m):
        """Check that device refresh works and reuses the same objects."""
        dc1_devid = 'RF:01'
        dc1a = DOOR_CONTACT.device(devid=dc1_devid, status=CONST.STATUS_ON)

        dc2_devid = 'RF:02'
        dc2a = DOOR_CONTACT.device(devid=dc2_devid, status=CONST.STATUS_OFF)

        m.post(CONST.LOGIN_URL, text=LOGIN.post_response_ok())
        m.get(CONST.OAUTH_TOKEN_URL, text=OAUTH_CLAIMS.get_response_ok())
        m.post(CONST.LOGOUT_URL, text=LOGOUT.post_response_ok())
        m.get(CONST.DEVICES_URL, text='[' + dc1a + ',' + dc2a + ']')
        m.get(CONST.PANEL_URL, text=PANEL.get_response_ok())

        # Reset
        self.abode.logout()

        # Get all devices
        self.abode.get_devices()

        # Get and check devices

        dc1a_dev = self.abode.get_device(dc1_devid)
        assert json.loads(dc1a)['id'] == dc1a_dev.device_id

        dc2a_dev = self.abode.get_device(dc2_devid)
        assert json.loads(dc2a)['id'] == dc2a_dev.device_id

        # Change device states
        dc1b = DOOR_CONTACT.device(devid=dc1_devid, status=CONST.STATUS_OFF)

        dc2b = DOOR_CONTACT.device(devid=dc2_devid, status=CONST.STATUS_ON)

        m.get(CONST.DEVICES_URL, text='[' + dc1b + ',' + dc2b + ']')

        # Refresh all devices
        self.abode.get_devices(refresh=True)

        # Get and check devices again, ensuring they are the same object
        # Future note: "if a is b" tests that the object is the same
        # Thus asserting dc1a_dev is dc1b_dev tests if they are the same object
        dc1b_dev = self.abode.get_device(dc1_devid)
        assert json.loads(dc1b)['id'] == dc1b_dev.device_id
        assert dc1a_dev is dc1b_dev

        dc2b_dev = self.abode.get_device(dc2_devid)
        assert json.loads(dc2b)['id'] == dc2b_dev.device_id
        assert dc2a_dev is dc2b_dev

    def tests_settings_validation(self, m):
        """Check that device panel general settings are working."""
        m.post(CONST.LOGIN_URL, text=LOGIN.post_response_ok())
        m.get(CONST.OAUTH_TOKEN_URL, text=OAUTH_CLAIMS.get_response_ok())
        m.post(CONST.LOGOUT_URL, text=LOGOUT.post_response_ok())
        m.get(CONST.PANEL_URL, text=PANEL.get_response_ok())
        m.get(CONST.SETTINGS_URL, text=MOCK.generic_response_ok())

        with pytest.raises(jaraco.abode.AbodeException):
            self.abode.set_setting("fliptrix", "foobar")

    def tests_general_settings(self, m):
        """Check that device panel general settings are working."""
        m.post(CONST.LOGIN_URL, text=LOGIN.post_response_ok())
        m.get(CONST.OAUTH_TOKEN_URL, text=OAUTH_CLAIMS.get_response_ok())
        m.post(CONST.LOGOUT_URL, text=LOGOUT.post_response_ok())
        m.get(CONST.PANEL_URL, text=PANEL.get_response_ok())
        m.put(CONST.SETTINGS_URL, text=MOCK.generic_response_ok())

        self.abode.set_setting(
            CONST.SETTING_CAMERA_RESOLUTION, CONST.SETTING_CAMERA_RES_640_480
        )

        self.abode.set_setting(CONST.SETTING_CAMERA_GRAYSCALE, CONST.SETTING_ENABLE)

        self.abode.set_setting(CONST.SETTING_SILENCE_SOUNDS, CONST.SETTING_ENABLE)

        with pytest.raises(jaraco.abode.AbodeException):
            self.abode.set_setting(CONST.SETTING_CAMERA_RESOLUTION, "foobar")

        with pytest.raises(jaraco.abode.AbodeException):
            self.abode.set_setting(CONST.SETTING_CAMERA_GRAYSCALE, "foobar")

        with pytest.raises(jaraco.abode.AbodeException):
            self.abode.set_setting(CONST.SETTING_SILENCE_SOUNDS, "foobar")

    def tests_area_settings(self, m):
        """Check that device panel areas settings are working."""
        m.post(CONST.LOGIN_URL, text=LOGIN.post_response_ok())
        m.get(CONST.OAUTH_TOKEN_URL, text=OAUTH_CLAIMS.get_response_ok())
        m.post(CONST.LOGOUT_URL, text=LOGOUT.post_response_ok())
        m.get(CONST.PANEL_URL, text=PANEL.get_response_ok())
        m.put(CONST.AREAS_URL, text=MOCK.generic_response_ok())

        self.abode.set_setting(
            CONST.SETTING_ENTRY_DELAY_AWAY, CONST.SETTING_ENTRY_EXIT_DELAY_10SEC
        )

        self.abode.set_setting(
            CONST.SETTING_EXIT_DELAY_AWAY, CONST.SETTING_ENTRY_EXIT_DELAY_30SEC
        )

        with pytest.raises(jaraco.abode.AbodeException):
            self.abode.set_setting(CONST.SETTING_ENTRY_DELAY_AWAY, "foobar")

        # 10 seconds is invalid here
        with pytest.raises(jaraco.abode.AbodeException):
            self.abode.set_setting(
                CONST.SETTING_EXIT_DELAY_AWAY, CONST.SETTING_ENTRY_EXIT_DELAY_10SEC
            )

    def tests_sound_settings(self, m):
        """Check that device panel sound settings are working."""
        m.post(CONST.LOGIN_URL, text=LOGIN.post_response_ok())
        m.get(CONST.OAUTH_TOKEN_URL, text=OAUTH_CLAIMS.get_response_ok())
        m.post(CONST.LOGOUT_URL, text=LOGOUT.post_response_ok())
        m.get(CONST.PANEL_URL, text=PANEL.get_response_ok())
        m.put(CONST.SOUNDS_URL, text=MOCK.generic_response_ok())

        self.abode.set_setting(CONST.SETTING_DOOR_CHIME, CONST.SETTING_SOUND_LOW)

        self.abode.set_setting(
            CONST.SETTING_ALARM_LENGTH, CONST.SETTING_ALARM_LENGTH_2MIN
        )

        self.abode.set_setting(
            CONST.SETTING_FINAL_BEEPS, CONST.SETTING_FINAL_BEEPS_3SEC
        )

        with pytest.raises(jaraco.abode.AbodeException):
            self.abode.set_setting(CONST.SETTING_DOOR_CHIME, "foobar")

        with pytest.raises(jaraco.abode.AbodeException):
            self.abode.set_setting(CONST.SETTING_ALARM_LENGTH, "foobar")

        with pytest.raises(jaraco.abode.AbodeException):
            self.abode.set_setting(CONST.SETTING_FINAL_BEEPS, "foobar")

    def tests_siren_settings(self, m):
        """Check that device panel siren settings are working."""
        m.post(CONST.LOGIN_URL, text=LOGIN.post_response_ok())
        m.get(CONST.OAUTH_TOKEN_URL, text=OAUTH_CLAIMS.get_response_ok())
        m.post(CONST.LOGOUT_URL, text=LOGOUT.post_response_ok())
        m.get(CONST.PANEL_URL, text=PANEL.get_response_ok())
        m.put(CONST.SIREN_URL, text=MOCK.generic_response_ok())

        self.abode.set_setting(
            CONST.SETTING_SIREN_ENTRY_EXIT_SOUNDS, CONST.SETTING_ENABLE
        )

        self.abode.set_setting(CONST.SETTING_SIREN_CONFIRM_SOUNDS, CONST.SETTING_ENABLE)

        self.abode.set_setting(CONST.SETTING_SIREN_TAMPER_SOUNDS, CONST.SETTING_ENABLE)

        with pytest.raises(jaraco.abode.AbodeException):
            self.abode.set_setting(CONST.SETTING_SIREN_ENTRY_EXIT_SOUNDS, "foobar")

        with pytest.raises(jaraco.abode.AbodeException):
            self.abode.set_setting(CONST.SETTING_SIREN_CONFIRM_SOUNDS, "foobar")

        with pytest.raises(jaraco.abode.AbodeException):
            self.abode.set_setting(CONST.SETTING_SIREN_TAMPER_SOUNDS, "foobar")

    @pytest.mark.usefixtures('cache_path')
    def tests_cookies(self, m):
        """Check that cookies are saved and loaded successfully."""
        m.post(CONST.LOGIN_URL, text=LOGIN.post_response_ok())
        m.get(CONST.OAUTH_TOKEN_URL, text=OAUTH_CLAIMS.get_response_ok())
        m.post(CONST.LOGOUT_URL, text=LOGOUT.post_response_ok())
        m.get(CONST.DEVICES_URL, text=DEVICES.EMPTY_DEVICE_RESPONSE)
        m.get(CONST.PANEL_URL, text=PANEL.get_response_ok())

        # Create abode
        abode = jaraco.abode.Abode(
            username='fizz',
            password='buzz',
            auto_login=False,
            get_devices=False,
            disable_cache=False,
            cache_path=self.cache_path,
        )

        # Mock cookie created by Abode after login
        cookie = requests.cookies.create_cookie(name='SESSION', value='COOKIE')

        abode._session.cookies.set_cookie(cookie)

        abode.login()

        # Test that our cookies are fully realized prior to login

        assert abode._cache['uuid'] is not None
        assert abode._cache['cookies'] is not None

        # Test that we now have a cookies file
        assert os.path.exists(self.cache_path)

        # Copy our current cookies file and data
        first_cookies_data = abode._cache

        # New abode instance reads in old data
        abode = jaraco.abode.Abode(
            username='fizz',
            password='buzz',
            auto_login=False,
            get_devices=False,
            disable_cache=False,
            cache_path=self.cache_path,
        )

        # Test that the cookie data is the same
        assert abode._cache['uuid'] == first_cookies_data['uuid']

    @pytest.mark.usefixtures('cache_path')
    def test_empty_cookies(self, m):
        """Check that empty cookies file is loaded successfully."""
        m.post(CONST.LOGIN_URL, text=LOGIN.post_response_ok())
        m.get(CONST.OAUTH_TOKEN_URL, text=OAUTH_CLAIMS.get_response_ok())
        m.post(CONST.LOGOUT_URL, text=LOGOUT.post_response_ok())
        m.get(CONST.DEVICES_URL, text=DEVICES.EMPTY_DEVICE_RESPONSE)
        m.get(CONST.PANEL_URL, text=PANEL.get_response_ok())

        # Create an empty file
        self.cache_path.write_text('')

        # Cookies are created
        empty_abode = jaraco.abode.Abode(
            username='fizz',
            password='buzz',
            auto_login=True,
            get_devices=False,
            disable_cache=False,
            cache_path=self.cache_path,
        )

        # Test that some cache exists

        assert empty_abode._cache['uuid'] is not None

    @pytest.mark.usefixtures('cache_path')
    def test_invalid_cookies(self, m):
        """Check that empty cookies file is loaded successfully."""
        m.post(CONST.LOGIN_URL, text=LOGIN.post_response_ok())
        m.get(CONST.OAUTH_TOKEN_URL, text=OAUTH_CLAIMS.get_response_ok())
        m.post(CONST.LOGOUT_URL, text=LOGOUT.post_response_ok())
        m.get(CONST.DEVICES_URL, text=DEVICES.EMPTY_DEVICE_RESPONSE)
        m.get(CONST.PANEL_URL, text=PANEL.get_response_ok())

        # Create an invalid pickle file
        self.cache_path.write_text('Invalid file goes here')

        # Cookies are created
        empty_abode = jaraco.abode.Abode(
            username='fizz',
            password='buzz',
            auto_login=True,
            get_devices=False,
            disable_cache=False,
            cache_path=self.cache_path,
        )

        # Test that some cache exists

        assert empty_abode._cache['uuid'] is not None
