import logging

from jaraco.collections import DictAdapter, Projection

from ._itertools import single


log = logging.getLogger(__name__)


class Stateful:
    def __init__(self, state, client):
        """Set up Abode device."""
        self._state = state
        self._client = client

    def __getattr__(self, name):
        try:
            return self._state[name]
        except KeyError as exc:
            raise AttributeError(name) from exc

    def update(self, state):
        """Update the local state from a new state.

        Only updates keys already present.
        """
        self._state.update(Projection(self._state, state))

    @property
    def desc(self):
        """Return a short description of self."""
        return self._desc_t.format_map(DictAdapter(self))

    def refresh(self, path=None):
        """Refresh the device state.

        Useful when not using the notification service.
        """
        tmpl = path or self._url_t
        path = tmpl.format(id=self.id)

        response = self._client.send_request(method="get", path=path)
        state = single(response.json())

        log.debug(f"{self.__class__.__name__} Refresh Response: %s", response.text)

        self._validate(state)
        self.update(state)

        return state

    def _validate(self, state):
        pass
