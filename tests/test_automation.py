"""Test the Abode device classes."""
import jaraco.abode
from jaraco.abode.helpers import urls
import pytest

from . import mock as MOCK
from .mock import login as LOGIN
from .mock import oauth_claims as OAUTH_CLAIMS
from .mock import logout as LOGOUT
from .mock import panel as PANEL
from .mock import automation as AUTOMATION


AID_1 = '47fae27488f74f55b964a81a066c3a01'
AID_2 = '47fae27488f74f55b964a81a066c3a02'
AID_3 = '47fae27488f74f55b964a81a066c3a03'


class TestAutomation:
    """Test the automation class."""

    def test_automation_init(self, m):
        """Check the Abode automation class init's properly."""
        # Set up URLs
        m.post(urls.LOGIN, json=LOGIN.post_response_ok())
        m.get(urls.OAUTH_TOKEN, json=OAUTH_CLAIMS.get_response_ok())
        m.post(urls.LOGOUT, json=LOGOUT.post_response_ok())
        m.get(urls.PANEL, json=PANEL.get_response_ok())

        # Set up automation
        automation_resp = AUTOMATION.get_response_ok(
            name='Auto Away',
            enabled=True,
            id=AID_1,
        )

        m.get(urls.AUTOMATION, json=automation_resp)

        # Logout to reset everything
        self.client.logout()

        # Get our specific automation
        automation = self.client.get_automation(AID_1)

        # Check automation states match
        assert automation is not None

        assert automation._state == automation_resp
        assert automation.id == str(automation_resp['id'])
        assert automation.name == automation_resp['name']
        assert automation.enabled == automation_resp['enabled']
        assert automation.desc is not None

    def test_automation_refresh(self, m):
        """Check the automation Abode class refreshes."""
        # Set up URLs
        m.post(urls.LOGIN, json=LOGIN.post_response_ok())
        m.get(urls.OAUTH_TOKEN, json=OAUTH_CLAIMS.get_response_ok())
        m.post(urls.LOGOUT, json=LOGOUT.post_response_ok())
        m.get(urls.PANEL, json=PANEL.get_response_ok())

        # Set up automation
        resp = [
            AUTOMATION.get_response_ok(name='Test Automation', enabled=True, id=AID_1)
        ]

        m.get(urls.AUTOMATION, json=resp)

        # Set up refreshed automation
        resp_changed = [
            AUTOMATION.get_response_ok(
                name='Test Automation Changed',
                enabled=False,
                id=AID_1,
            )
        ]

        automation_id_url = urls.AUTOMATION_ID.format(id=resp[0]['id'])

        m.get(automation_id_url, json=resp_changed)

        # Logout to reset everything
        self.client.logout()

        # Get the first automation and test
        automation = self.client.get_automation(AID_1)

        # Check automation states match

        assert automation is not None
        assert automation._state == resp[0]

        # Refresh and retest
        automation.refresh()
        assert automation._state == resp_changed[0]

        # Refresh with get_automation() and test
        resp_changed = [
            AUTOMATION.get_response_ok(
                name='Test Automation Changed Again',
                enabled=True,
                id=AID_1,
            )
        ]

        m.get(automation_id_url, json=resp_changed)

        # Refresh and retest
        automation = self.client.get_automation(AID_1, refresh=True)

        assert automation._state == resp_changed[0]

        # Test refresh returning an incorrect ID throws exception
        # Set up refreshed automation
        resp_changed = [
            AUTOMATION.get_response_ok(
                name='Test Automation Changed',
                enabled=False,
                id='47fae27488f74f55b964a81a066c3a11',
            )
        ]

        m.get(automation_id_url, json=resp_changed)

        with pytest.raises(jaraco.abode.Exception):
            automation.refresh()

    def test_multiple_automations(self, m):
        """Check that multiple automations work and return correctly."""
        # Set up URLs
        m.post(urls.LOGIN, json=LOGIN.post_response_ok())
        m.get(urls.OAUTH_TOKEN, json=OAUTH_CLAIMS.get_response_ok())
        m.post(urls.LOGOUT, json=LOGOUT.post_response_ok())
        m.get(urls.PANEL, json=PANEL.get_response_ok())

        # Set up automations
        resp = [
            AUTOMATION.get_response_ok(
                name='Test Automation One',
                enabled=True,
                id=AID_1,
            ),
            AUTOMATION.get_response_ok(
                name='Test Automation Two',
                enabled=True,
                id=AID_2,
            ),
            AUTOMATION.get_response_ok(
                name='Test Automation Three',
                enabled=True,
                id=AID_3,
            ),
        ]

        m.get(urls.AUTOMATION, json=resp)

        # Logout to reset everything
        self.client.logout()

        # Test that the automations return the correct number
        automations = self.client.get_automations()
        assert len(automations) == 3

        # Get the first automation and test

        automation_1 = self.client.get_automation(AID_1)
        assert automation_1 is not None
        assert automation_1._state == resp[0]

        automation_2 = self.client.get_automation(AID_2)
        assert automation_2 is not None
        assert automation_2._state == resp[1]

        automation_3 = self.client.get_automation(AID_3)
        assert automation_3 is not None
        assert automation_3._state == resp[2]

    def test_automation_class_reuse(self, m):
        """Check that automations reuse the same classes when refreshed."""
        # Set up URLs
        m.post(urls.LOGIN, json=LOGIN.post_response_ok())
        m.get(urls.OAUTH_TOKEN, json=OAUTH_CLAIMS.get_response_ok())
        m.post(urls.LOGOUT, json=LOGOUT.post_response_ok())
        m.get(urls.PANEL, json=PANEL.get_response_ok())

        # Set up automations
        resp = [
            AUTOMATION.get_response_ok(
                name='Test Automation One',
                enabled=True,
                id=AID_1,
            ),
            AUTOMATION.get_response_ok(
                name='Test Automation Two',
                enabled=True,
                id=AID_2,
            ),
        ]

        m.get(urls.AUTOMATION, json=resp)

        # Logout to reset everything
        self.client.logout()

        # Test that the automations return the correct number
        automations = self.client.get_automations()
        assert len(automations) == 2

        # Get the automations and test

        automation_1 = self.client.get_automation(AID_1)
        assert automation_1 is not None
        assert automation_1._state == resp[0]

        automation_2 = self.client.get_automation(AID_2)
        assert automation_2 is not None
        assert automation_2._state == resp[1]

        # Update the automations
        resp = [
            AUTOMATION.get_response_ok(
                name='Test Automation One Changed',
                enabled=False,
                id=AID_1,
            ),
            AUTOMATION.get_response_ok(
                name='Test Automation Two Changed',
                enabled=False,
                id=AID_2,
            ),
            AUTOMATION.get_response_ok(
                name='Test Automation Three New',
                enabled=True,
                id=AID_3,
            ),
        ]

        m.get(urls.AUTOMATION, json=resp)

        # Update
        automations_changed = self.client.get_automations(refresh=True)
        assert len(automations_changed) == 3

        # Check that the original two automations have updated
        # and are using the same class
        automation_1_changed = self.client.get_automation(AID_1)
        assert automation_1_changed is not None
        assert automation_1_changed._state == resp[0]
        assert automation_1 is automation_1_changed

        automation_2_changed = self.client.get_automation(AID_2)
        assert automation_2_changed is not None
        assert automation_2_changed._state == resp[1]
        assert automation_2 is automation_2_changed

        # Check that the third new automation is correct
        automation_3 = self.client.get_automation(AID_3)
        assert automation_3 is not None
        assert automation_3._state == resp[2]

    def test_automation_enable(self, m):
        """Check that automations can change their enable state."""
        # Set up URLs
        m.post(urls.LOGIN, json=LOGIN.post_response_ok())
        m.get(urls.OAUTH_TOKEN, json=OAUTH_CLAIMS.get_response_ok())
        m.post(urls.LOGOUT, json=LOGOUT.post_response_ok())
        m.get(urls.PANEL, json=PANEL.get_response_ok())

        # Set up automation
        resp = [
            AUTOMATION.get_response_ok(
                name='Test Automation One',
                enabled=True,
                id=AID_1,
            )
        ]

        m.get(urls.AUTOMATION, json=resp)

        # Logout to reset everything
        self.client.logout()

        # Get the automation and test

        automation = self.client.get_automation(AID_1)
        assert automation is not None
        assert automation._state == resp[0]
        assert automation.enabled

        # Set up our active state change and URL
        set_active_url = urls.AUTOMATION_ID.format(id=resp[0]['id'])

        m.patch(
            set_active_url,
            json=AUTOMATION.get_response_ok(
                name='Test Automation One',
                enabled=False,
                id=AID_1,
            ),
        )

        # Test the changed state
        automation.enable(False)
        assert not automation.enabled

        # Change the state back, this time with an array response
        m.patch(
            set_active_url,
            json=[
                AUTOMATION.get_response_ok(
                    name='Test Automation One',
                    enabled=True,
                    id=AID_1,
                )
            ],
        )

        # Test the changed state
        automation.enable(True)
        assert automation.enabled

        # Test that the response returns the wrong state
        m.patch(
            set_active_url,
            json=[
                AUTOMATION.get_response_ok(
                    name='Test Automation One',
                    enabled=True,
                    id=AID_1,
                )
            ],
        )

        with pytest.raises(jaraco.abode.Exception):
            automation.enable(False)

        # Test that the response returns the wrong id
        m.patch(
            set_active_url,
            json=[
                AUTOMATION.get_response_ok(
                    name='Test Automation One',
                    enabled=True,
                    id=AID_2,
                )
            ],
        )

        with pytest.raises(jaraco.abode.Exception):
            automation.enable(True)

    def test_automation_trigger(self, m):
        """Check that automations can be triggered."""
        # Set up URLs
        m.post(urls.LOGIN, json=LOGIN.post_response_ok())
        m.get(urls.OAUTH_TOKEN, json=OAUTH_CLAIMS.get_response_ok())
        m.post(urls.LOGOUT, json=LOGOUT.post_response_ok())
        m.get(urls.PANEL, json=PANEL.get_response_ok())

        # Set up automation
        resp = [
            AUTOMATION.get_response_ok(
                name='Test Automation One',
                enabled=True,
                id=AID_1,
            ),
        ]

        m.get(urls.AUTOMATION, json=resp)

        # Logout to reset everything
        self.client.logout()

        # Get the automation and test

        automation = self.client.get_automation(AID_1)
        assert automation is not None

        # Set up our automation trigger reply
        set_active_url = urls.AUTOMATION_APPLY.format(id=automation.id)
        m.post(set_active_url, json=MOCK.generic_response_ok())

        # Test triggering
        automation.trigger()
