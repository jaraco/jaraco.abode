"""Representation of an automation configured in Abode."""
import logging

import jaraco.abode

from ._itertools import single
from .helpers import urls
from .helpers import errors as ERROR
from .devices.base import Device

log = logging.getLogger(__name__)


class Automation:
    """Class for viewing and controlling automations."""

    def __init__(self, abode, state):
        self._client = abode
        self._state = state

    def enable(self, enable: bool):
        """Enable or disable the automation."""
        path = urls.AUTOMATION_ID.format(id=self.automation_id)

        response = self._client.send_request(
            method="patch", path=path, data={'enabled': enable}
        )

        state = single(response.json())

        assert isinstance(state['enabled'], bool)

        if state['id'] != self._state['id'] or state['enabled'] != enable:
            raise jaraco.abode.Exception(ERROR.INVALID_AUTOMATION_EDIT_RESPONSE)

        self.update(state)

        log.info("Set automation %s enable to: %s", self.name, self.is_enabled)
        log.debug("Automation response: %s", response.text)

    def trigger(self):
        """Trigger the automation."""
        path = urls.AUTOMATION_APPLY.format(id=self.automation_id)

        self._client.send_request(method="post", path=path)

        log.info("Automation triggered: %s", self.name)

    def refresh(self):
        """Refresh the automation."""
        path = urls.AUTOMATION_ID.format(id=self.automation_id)

        response = self._client.send_request(method="get", path=path)
        response_object = single(response.json())

        if str(response_object['id']) != self.automation_id:
            raise jaraco.abode.Exception(ERROR.INVALID_AUTOMATION_REFRESH_RESPONSE)

        self.update(response_object)

    def update(self, automation):
        """Update the internal automation json."""
        Device.update(self, automation)

    @property
    def automation_id(self):
        """Get the id of the automation."""
        return str(self._state['id'])

    @property
    def name(self):
        """Get the name of the automation."""
        return self._state['name']

    @property
    def is_enabled(self):
        """Return True if the automation is enabled."""
        return self._state['enabled']

    @property
    def desc(self):
        """Get a short description of the automation."""
        return '{} (ID: {}, Enabled: {})'.format(
            self.name, self.automation_id, self.is_enabled
        )
