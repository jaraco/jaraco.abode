from jaraco.collections import Projection


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
