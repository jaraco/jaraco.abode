"""Test the Abode device classes."""
import jaraco.abode
from jaraco.abode.helpers import urls
import pytest

from .mock import login as LOGIN
from .mock import oauth_claims as OAUTH_CLAIMS
from .mock import logout as LOGOUT
from .mock import panel as PANEL
from .mock import devices as DEVICES
from .mock.devices import alarm as ALARM


class TestAlarm:
    """Test the Alarm class."""

    def test_abode_alarm_setup(self, m):
        """Check that Abode alarm device is set up properly."""
        panel = PANEL.get_response_ok(mode='standby')
        alarm = ALARM.device(area='1', panel=panel)

        m.post(urls.LOGIN, json=LOGIN.post_response_ok())
        m.get(urls.OAUTH_TOKEN, json=OAUTH_CLAIMS.get_response_ok())
        m.get(urls.DEVICES, json=DEVICES.EMPTY_DEVICE_RESPONSE)
        m.get(urls.PANEL, json=PANEL.get_response_ok())

        alarm_device = self.client.get_alarm()

        assert alarm_device is not None

        assert alarm_device._state == alarm

    def test_alarm_device_properties(self, m):
        """Check that the abode device properties are working."""
        # Set up URLs
        m.post(urls.LOGIN, json=LOGIN.post_response_ok())
        m.get(urls.OAUTH_TOKEN, json=OAUTH_CLAIMS.get_response_ok())
        m.post(urls.LOGOUT, json=LOGOUT.post_response_ok())
        m.get(
            urls.PANEL,
            json=PANEL.get_response_ok(
                mode='standby',
                battery=True,
                is_cellular=True,
                mac='01:AA:b3:C4:d5:66',
            ),
        )
        m.get(urls.DEVICES, json=DEVICES.EMPTY_DEVICE_RESPONSE)

        # Logout to reset everything
        self.client.logout()

        # Get alarm and test
        alarm = self.client.get_alarm()
        assert alarm.id == 'area_1'
        assert alarm is not None
        assert alarm.mode == 'standby'
        assert alarm.status == 'standby'
        assert alarm.battery
        assert alarm.is_cellular
        assert not alarm.is_on
        assert alarm.uuid == '01aab3c4d566'
        assert alarm.mac_address == '01:AA:b3:C4:d5:66'

        # Change alarm properties and state to away and test
        m.get(
            urls.PANEL,
            json=PANEL.get_response_ok(mode='away', battery=False, is_cellular=False),
        )

        # Refresh alarm and test
        alarm.refresh()

        assert alarm.id == 'area_1'
        assert alarm.mode == 'away'
        assert alarm.status == 'away'
        assert not alarm.battery
        assert not alarm.is_cellular
        assert alarm.is_on

        # Change alarm state to final on state and test
        m.get(urls.PANEL, json=PANEL.get_response_ok(mode='home'))

        # Refresh alarm and test
        alarm.refresh()
        assert alarm.mode == 'home'
        assert alarm.status == 'home'
        assert alarm.is_on

    def test_alarm_device_mode_changes(self, m):
        """Test that the abode alarm can change/report modes."""
        # Set up URLs
        m.post(urls.LOGIN, json=LOGIN.post_response_ok())
        m.get(urls.OAUTH_TOKEN, json=OAUTH_CLAIMS.get_response_ok())
        m.post(urls.LOGOUT, json=LOGOUT.post_response_ok())
        m.get(urls.PANEL, json=PANEL.get_response_ok(mode='standby'))
        m.get(urls.DEVICES, json=DEVICES.EMPTY_DEVICE_RESPONSE)

        # Logout to reset everything
        self.client.logout()

        # Assert that after login we have our alarm device with standby mode
        alarm = self.client.get_alarm()

        assert alarm is not None
        assert alarm.status == 'standby'

        # Set mode URLs
        m.put(
            urls.panel_mode('1', 'standby'),
            json=PANEL.put_response_ok(mode='standby'),
        )
        m.put(
            urls.panel_mode('1', 'away'),
            json=PANEL.put_response_ok(mode='away'),
        )
        m.put(
            urls.panel_mode('1', 'home'),
            json=PANEL.put_response_ok(mode='home'),
        )

        # Set and test text based mode changes
        assert alarm.set_mode('home')
        assert alarm.mode == 'home'
        assert not alarm.is_standby
        assert alarm.is_home
        assert not alarm.is_away

        assert alarm.set_mode('away')
        assert alarm.mode == 'away'
        assert not alarm.is_standby
        assert not alarm.is_home
        assert alarm.is_away

        assert alarm.set_mode('standby')
        assert alarm.mode == 'standby'
        assert alarm.is_standby
        assert not alarm.is_home
        assert not alarm.is_away

        # Set and test direct mode changes
        assert alarm.set_home()
        assert alarm.mode == 'home'
        assert not alarm.is_standby
        assert alarm.is_home
        assert not alarm.is_away

        assert alarm.set_away()
        assert alarm.mode == 'away'
        assert not alarm.is_standby
        assert not alarm.is_home
        assert alarm.is_away

        assert alarm.set_standby()
        assert alarm.mode == 'standby'
        assert alarm.is_standby
        assert not alarm.is_home
        assert not alarm.is_away

        # Set and test default mode changes
        assert alarm.switch_off()
        assert alarm.mode == 'standby'
        assert alarm.is_standby
        assert not alarm.is_home
        assert not alarm.is_away

        self.client.set_default_mode('home')
        assert alarm.switch_on()
        assert alarm.mode == 'home'
        assert not alarm.is_standby
        assert alarm.is_home
        assert not alarm.is_away

        assert alarm.switch_off()
        assert alarm.mode == 'standby'
        assert alarm.is_standby
        assert not alarm.is_home
        assert not alarm.is_away

        self.client.set_default_mode('away')
        assert alarm.switch_on()
        assert alarm.mode == 'away'
        assert not alarm.is_standby
        assert not alarm.is_home
        assert alarm.is_away

        # Test that no mode throws exception
        with pytest.raises(jaraco.abode.Exception):
            alarm.set_mode(mode=None)

        # Test that an invalid mode throws exception
        with pytest.raises(jaraco.abode.Exception):
            alarm.set_mode('chestnuts')

        # Test that an invalid mode change response throws exception
        m.put(
            urls.panel_mode('1', 'home'),
            json=PANEL.put_response_ok(mode='away'),
        )

        with pytest.raises(jaraco.abode.Exception):
            alarm.set_mode('home')

        # Test that an invalid area in mode change response throws exception
        m.put(
            urls.panel_mode('1', 'home'),
            json=PANEL.put_response_ok(area='2', mode='home'),
        )

        with pytest.raises(jaraco.abode.Exception):
            alarm.set_mode('home')
