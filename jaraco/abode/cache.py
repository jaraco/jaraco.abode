import pickle
import logging


log = logging.getLogger(__name__)


def save_cache(data, filename):
    """Save cookies to a file."""
    with open(filename, 'wb') as handle:
        pickle.dump(data, handle)


def load_cache(filename):
    """Load cookies from a file."""
    with open(filename, 'rb') as handle:
        try:
            return pickle.load(handle)
        except EOFError:
            log.warning("Empty pickle file: %s", filename)
        except (pickle.UnpicklingError, ValueError):
            log.warning("Corrupted pickle file: %s", filename)
