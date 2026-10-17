from jaraco.abode.socketio import SocketIO


def test_handle_event_captures_callback_exception(caplog):
    sio = SocketIO('wss://example.invalid')
    received = []

    def _bad_callback(*args):
        raise RuntimeError("CHAOS!!!")

    sio.on('event', _bad_callback)
    sio.on('event', received.append)

    sio._handle_event('event', 'data')

    assert received == ['data']
    assert 'Captured exception during SocketIO event callback' in caplog.text
