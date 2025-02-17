import functools
import urllib.parse

import pytest
import responses

import jaraco.abode
from jaraco.abode.helpers import urls


@pytest.fixture(autouse=True)
def instance_client(request):
    if request.instance is None:
        return

    request.instance.client = jaraco.abode.Client(
        username='foobar',
        password='deadbeef',
    )


def make_headers(cookies):
    return (('Set-Cookie', f'{key}={value}') for key, value in cookies.items())


class DefaultLocMock(responses.RequestsMock):
    """
    Wrap responses.add to give it all URLs a default scheme and netloc.
    """

    def add(self, method, url, *args, headers={}, cookies={}, **kwargs):
        default = urllib.parse.urlparse(urls.BASE)
        parsed = urllib.parse.urlparse(url)
        scheme = parsed.scheme or default.scheme
        netloc = parsed.netloc or default.netloc
        replaced = urllib.parse.urlunparse(
            parsed._replace(scheme=scheme, netloc=netloc)
        )
        headers = tuple(headers.items()) + tuple(make_headers(cookies))
        return super().add(method, replaced, *args, headers=headers, **kwargs)

    delete = functools.partialmethod(add, responses.DELETE)
    get = functools.partialmethod(add, responses.GET)
    head = functools.partialmethod(add, responses.HEAD)
    options = functools.partialmethod(add, responses.OPTIONS)
    patch = functools.partialmethod(add, responses.PATCH)
    post = functools.partialmethod(add, responses.POST)
    put = functools.partialmethod(add, responses.PUT)


def wrap_mock_default_loc(mocker):
    if not isinstance(mocker, DefaultLocMock):
        mocker.__class__ = DefaultLocMock
    return mocker


@pytest.fixture
def m(responses):
    return wrap_mock_default_loc(responses)


@pytest.fixture(autouse=True)
def app_paths(tmp_path, monkeypatch):
    """
    Redirect app dirs to temporary paths.
    """

    class Paths:
        user_data_path = tmp_path / 'user data'

        @property
        def user_data(self):
            self.user_data_path.mkdir(exist_ok=True)
            return self.user_data_path

    monkeypatch.setattr(jaraco.abode.config, 'paths', Paths())


@pytest.fixture
def all_devices(m):
    # Set up URLs
    import tests.mock.devices.door_contact
    import tests.mock.devices.door_lock
    import tests.mock.devices.glass
    import tests.mock.devices.ir_camera
    import tests.mock.devices.keypad
    import tests.mock.devices.pir
    import tests.mock.devices.power_switch_meter
    import tests.mock.devices.power_switch_sensor
    import tests.mock.devices.remote_controller
    import tests.mock.devices.secure_barrier
    import tests.mock.devices.siren
    import tests.mock.devices.status_display
    import tests.mock.devices.water_sensor
    import tests.mock.login
    import tests.mock.logout
    import tests.mock.oauth_claims
    import tests.mock.panel

    m.post(jaraco.abode.helpers.urls.LOGIN, json=tests.mock.login.post_response_ok())
    m.get(
        jaraco.abode.helpers.urls.OAUTH_TOKEN,
        json=tests.mock.oauth_claims.get_response_ok(),
    )
    m.get(
        jaraco.abode.helpers.urls.PANEL,
        json=tests.mock.panel.get_response_ok(mode='standby'),
    )

    # Create all devices
    all_devices = [
        tests.mock.devices.door_contact.device(),
        tests.mock.devices.door_lock.device(),
        tests.mock.devices.glass.device(),
        tests.mock.devices.ir_camera.device(),
        tests.mock.devices.keypad.device(),
        tests.mock.devices.pir.device(),
        tests.mock.devices.power_switch_meter.device(),
        tests.mock.devices.power_switch_sensor.device(),
        tests.mock.devices.remote_controller.device(),
        tests.mock.devices.secure_barrier.device(),
        tests.mock.devices.siren.device(),
        tests.mock.devices.status_display.device(),
        tests.mock.devices.water_sensor.device(),
    ]

    m.get(jaraco.abode.helpers.urls.DEVICES, json=all_devices)
