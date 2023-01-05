"""Representation of an automation configured in Abode."""
import logging

import jaraco

from ._itertools import single
from .helpers import urls
from .helpers import errors as ERROR

_LOGGER = logging.getLogger(__name__)


class Automation:
    """Class for viewing and controlling automations."""

    def __init__(self, abode, automation):
        self._client = abode
        self._automation = automation

    def enable(self, enable):
        """Enable or disable the automation."""
        path = urls.AUTOMATION_ID.format(id=self.automation_id)

        self._automation['enabled'] = enable

        response = self._client.send_request(
            method="patch", path=path, data={'enabled': enable}
        )

        response_object = single(response.json())

        if str(response_object['id']) != str(self._automation['id']) or str(
            response_object['enabled']
        ) != str(self._automation['enabled']):
            raise jaraco.abode.Exception(ERROR.INVALID_AUTOMATION_EDIT_RESPONSE)

        self.update(response_object)

        _LOGGER.info("Set automation %s enable to: %s", self.name, self.is_enabled)
        _LOGGER.debug("Automation response: %s", response.text)

    def trigger(self):
        """Trigger the automation."""
        path = urls.AUTOMATION_APPLY.format(id=self.automation_id)

        self._client.send_request(method="post", path=path)

        _LOGGER.info("Automation triggered: %s", self.name)

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
        self._automation.update(
            {k: automation[k] for k in automation if self._automation.get(k)}
        )

    @property
    def automation_id(self):
        """Get the id of the automation."""
        return str(self._automation['id'])

    @property
    def name(self):
        """Get the name of the automation."""
        return self._automation['name']

    @property
    def is_enabled(self):
        """Return True if the automation is enabled."""
        return self._automation['enabled']

    @property
    def desc(self):
        """Get a short description of the automation."""
        return '{} (ID: {}, Enabled: {})'.format(
            self.name, self.automation_id, self.is_enabled
        )
