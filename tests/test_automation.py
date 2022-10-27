"""Test the Abode device classes."""
import json

import jaraco.abode
import jaraco.abode.helpers.constants as CONST
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

    def tests_automation_init(self, m):
        """Check the Abode automation class init's properly."""
        # Set up URLs
        m.post(CONST.LOGIN_URL, text=LOGIN.post_response_ok())
        m.get(CONST.OAUTH_TOKEN_URL, text=OAUTH_CLAIMS.get_response_ok())
        m.post(CONST.LOGOUT_URL, text=LOGOUT.post_response_ok())
        m.get(CONST.PANEL_URL, text=PANEL.get_response_ok())

        # Set up automation
        automation_text = AUTOMATION.get_response_ok(
            name='Auto Away', enabled=True, aid=AID_1
        )

        automation_json = json.loads(automation_text)

        m.get(CONST.AUTOMATION_URL, text=automation_text)

        # Logout to reset everything
        self.abode.logout()

        # Get our specific automation
        automation = self.abode.get_automation(AID_1)

        # Check automation states match
        assert automation is not None

        assert automation._automation == automation_json
        assert automation.automation_id == str(automation_json['id'])
        assert automation.name == automation_json['name']
        assert automation.is_enabled == automation_json['enabled']
        assert automation.desc is not None

    def tests_automation_refresh(self, m):
        """Check the automation Abode class refreshes."""
        # Set up URL's
        m.post(CONST.LOGIN_URL, text=LOGIN.post_response_ok())
        m.get(CONST.OAUTH_TOKEN_URL, text=OAUTH_CLAIMS.get_response_ok())
        m.post(CONST.LOGOUT_URL, text=LOGOUT.post_response_ok())
        m.get(CONST.PANEL_URL, text=PANEL.get_response_ok())

        # Set up automation
        automation_text = (
            '['
            + AUTOMATION.get_response_ok(
                name='Test Automation', enabled=True, aid=AID_1
            )
            + ']'
        )

        automation_json = json.loads(automation_text)

        m.get(CONST.AUTOMATION_URL, text=automation_text)

        # Set up refreshed automation
        automation_text_changed = (
            '['
            + AUTOMATION.get_response_ok(
                name='Test Automation Changed', enabled=False, aid=AID_1
            )
            + ']'
        )

        automation_json_changed = json.loads(automation_text_changed)

        automation_id_url = CONST.AUTOMATION_ID_URL.format(id=automation_json[0]['id'])

        m.get(automation_id_url, text=automation_text_changed)

        # Logout to reset everything
        self.abode.logout()

        # Get the first automation and test
        automation = self.abode.get_automation(AID_1)

        # Check automation states match

        assert automation is not None
        assert automation._automation == automation_json[0]

        # Refresh and retest
        automation.refresh()
        assert automation._automation == automation_json_changed[0]

        # Refresh with get_automation() and test
        automation_text_changed = (
            '['
            + AUTOMATION.get_response_ok(
                name='Test Automation Changed Again', enabled=True, aid=AID_1
            )
            + ']'
        )

        automation_json_changed = json.loads(automation_text_changed)
        m.get(automation_id_url, text=automation_text_changed)

        # Refresh and retest
        automation = self.abode.get_automation(AID_1, refresh=True)

        assert automation._automation == automation_json_changed[0]

        # Test refresh returning an incorrect ID throws exception
        # Set up refreshed automation
        automation_text_changed = (
            '['
            + AUTOMATION.get_response_ok(
                name='Test Automation Changed',
                enabled=False,
                aid='47fae27488f74f55b964a81a066c3a11',
            )
            + ']'
        )

        m.get(automation_id_url, text=automation_text_changed)

        with pytest.raises(jaraco.abode.AbodeException):
            automation.refresh()

    def tests_multiple_automations(self, m):
        """Check that multiple automations work and return correctly."""
        # Set up URL's
        m.post(CONST.LOGIN_URL, text=LOGIN.post_response_ok())
        m.get(CONST.OAUTH_TOKEN_URL, text=OAUTH_CLAIMS.get_response_ok())
        m.post(CONST.LOGOUT_URL, text=LOGOUT.post_response_ok())
        m.get(CONST.PANEL_URL, text=PANEL.get_response_ok())

        # Set up automations
        automation_text = (
            '['
            + AUTOMATION.get_response_ok(
                name='Test Automation One', enabled=True, aid=AID_1
            )
            + ','
            + AUTOMATION.get_response_ok(
                name='Test Automation Two', enabled=True, aid=AID_2
            )
            + ','
            + AUTOMATION.get_response_ok(
                name='Test Automation Three', enabled=True, aid=AID_3
            )
            + ']'
        )

        automation_json = json.loads(automation_text)

        m.get(CONST.AUTOMATION_URL, text=automation_text)

        # Logout to reset everything
        self.abode.logout()

        # Test that the automations return the correct number
        automations = self.abode.get_automations()
        assert len(automations) == 3

        # Get the first automation and test

        automation_1 = self.abode.get_automation(AID_1)
        assert automation_1 is not None
        assert automation_1._automation == automation_json[0]

        automation_2 = self.abode.get_automation(AID_2)
        assert automation_2 is not None
        assert automation_2._automation == automation_json[1]

        automation_3 = self.abode.get_automation(AID_3)
        assert automation_3 is not None
        assert automation_3._automation == automation_json[2]

    def tests_automation_class_reuse(self, m):
        """Check that automations reuse the same classes when refreshed."""
        # Set up URL's
        m.post(CONST.LOGIN_URL, text=LOGIN.post_response_ok())
        m.get(CONST.OAUTH_TOKEN_URL, text=OAUTH_CLAIMS.get_response_ok())
        m.post(CONST.LOGOUT_URL, text=LOGOUT.post_response_ok())
        m.get(CONST.PANEL_URL, text=PANEL.get_response_ok())

        # Set up automations
        automation_text = (
            '['
            + AUTOMATION.get_response_ok(
                name='Test Automation One', enabled=True, aid=AID_1
            )
            + ','
            + AUTOMATION.get_response_ok(
                name='Test Automation Two', enabled=True, aid=AID_2
            )
            + ']'
        )

        automation_json = json.loads(automation_text)

        m.get(CONST.AUTOMATION_URL, text=automation_text)

        # Logout to reset everything
        self.abode.logout()

        # Test that the automations return the correct number
        automations = self.abode.get_automations()
        assert len(automations) == 2

        # Get the automations and test

        automation_1 = self.abode.get_automation(AID_1)
        assert automation_1 is not None
        assert automation_1._automation == automation_json[0]

        automation_2 = self.abode.get_automation(AID_2)
        assert automation_2 is not None
        assert automation_2._automation == automation_json[1]

        # Update the automations
        automation_text = (
            '['
            + AUTOMATION.get_response_ok(
                name='Test Automation One Changed', enabled=False, aid=AID_1
            )
            + ','
            + AUTOMATION.get_response_ok(
                name='Test Automation Two Changed', enabled=False, aid=AID_2
            )
            + ','
            + AUTOMATION.get_response_ok(
                name='Test Automation Three New', enabled=True, aid=AID_3
            )
            + ']'
        )

        automation_json_changed = json.loads(automation_text)

        m.get(CONST.AUTOMATION_URL, text=automation_text)

        # Update
        automations_changed = self.abode.get_automations(refresh=True)
        assert len(automations_changed) == 3

        # Check that the original two automations have updated
        # and are using the same class
        automation_1_changed = self.abode.get_automation(AID_1)
        assert automation_1_changed is not None
        assert automation_1_changed._automation == automation_json_changed[0]
        assert automation_1 is automation_1_changed

        automation_2_changed = self.abode.get_automation(AID_2)
        assert automation_2_changed is not None
        assert automation_2_changed._automation == automation_json_changed[1]
        assert automation_2 is automation_2_changed

        # Check that the third new automation is correct
        automation_3 = self.abode.get_automation(AID_3)
        assert automation_3 is not None
        assert automation_3._automation == automation_json_changed[2]

    def tests_automation_enable(self, m):
        """Check that automations can change their enable state."""
        # Set up URL's
        m.post(CONST.LOGIN_URL, text=LOGIN.post_response_ok())
        m.get(CONST.OAUTH_TOKEN_URL, text=OAUTH_CLAIMS.get_response_ok())
        m.post(CONST.LOGOUT_URL, text=LOGOUT.post_response_ok())
        m.get(CONST.PANEL_URL, text=PANEL.get_response_ok())

        # Set up automation
        automation_text = (
            '['
            + AUTOMATION.get_response_ok(
                name='Test Automation One', enabled=True, aid=AID_1
            )
            + ']'
        )

        automation_json = json.loads(automation_text)

        m.get(CONST.AUTOMATION_URL, text=automation_text)

        # Logout to reset everything
        self.abode.logout()

        # Get the automation and test

        automation = self.abode.get_automation(AID_1)
        assert automation is not None
        assert automation._automation == automation_json[0]
        assert automation.is_enabled

        # Set up our active state change and URL
        set_active_url = CONST.AUTOMATION_ID_URL.format(id=automation_json[0]['id'])

        m.patch(
            set_active_url,
            text=AUTOMATION.get_response_ok(
                name='Test Automation One', enabled=False, aid=AID_1
            ),
        )

        # Test the changed state
        automation.enable(False)
        assert not automation.is_enabled

        # Change the state back, this time with an array response
        m.patch(
            set_active_url,
            text='['
            + AUTOMATION.get_response_ok(
                name='Test Automation One', enabled=True, aid=AID_1
            )
            + ']',
        )

        # Test the changed state
        automation.enable(True)
        assert automation.is_enabled

        # Test that the response returns the wrong state
        m.patch(
            set_active_url,
            text='['
            + AUTOMATION.get_response_ok(
                name='Test Automation One', enabled=True, aid=AID_1
            )
            + ']',
        )

        with pytest.raises(jaraco.abode.AbodeException):
            automation.enable(False)

        # Test that the response returns the wrong id
        m.patch(
            set_active_url,
            text='['
            + AUTOMATION.get_response_ok(
                name='Test Automation One', enabled=True, aid=AID_2
            )
            + ']',
        )

        with pytest.raises(jaraco.abode.AbodeException):
            automation.enable(True)

    def tests_automation_trigger(self, m):
        """Check that automations can be triggered."""
        # Set up URL's
        m.post(CONST.LOGIN_URL, text=LOGIN.post_response_ok())
        m.get(CONST.OAUTH_TOKEN_URL, text=OAUTH_CLAIMS.get_response_ok())
        m.post(CONST.LOGOUT_URL, text=LOGOUT.post_response_ok())
        m.get(CONST.PANEL_URL, text=PANEL.get_response_ok())

        # Set up automation
        automation_text = (
            '['
            + AUTOMATION.get_response_ok(
                name='Test Automation One', enabled=True, aid=AID_1
            )
            + ']'
        )

        m.get(CONST.AUTOMATION_URL, text=automation_text)

        # Logout to reset everything
        self.abode.logout()

        # Get the automation and test

        automation = self.abode.get_automation(AID_1)
        assert automation is not None

        # Set up our automation trigger reply
        set_active_url = CONST.AUTOMATION_APPLY_URL.format(id=automation.automation_id)
        m.post(set_active_url, text=MOCK.generic_response_ok())

        # Test triggering
        automation.trigger()
