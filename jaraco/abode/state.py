from jaraco.collections import DictAdapter, Projection


class Stateful:
    def __getattr__(self, name):
        try:
            return self._state[name]
        except KeyError as exc:
            raise AttributeError(name) from exc

    def update(self, json_state):
        """Update the json data from a dictionary.

        Only updates keys already present.
        """
        self._state.update(Projection(self._state, json_state))

    @property
    def desc(self):
        """Return a short description of self."""
        return self._desc_t.format_map(DictAdapter(self))
