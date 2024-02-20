import urllib.parse

import pytest
import jaraco.abode


@pytest.fixture(autouse=True)
def instance_client(request):
    if request.instance is None:
        return

    request.instance.client = jaraco.abode.Client(
        username='foobar',
        password='deadbeef',
    )


def wrap_mock_register_uri(mocker):
    """
    Allow path to omit the leading /
    """
    orig = mocker.register_uri

    def register_uri(method, url, *args, **kwargs):
        if not urllib.parse.urlparse(url).path.startswith('/'):
            url = '/' + url
        return orig(method, url, *args, **kwargs)

    mocker.register_uri = register_uri
    return mocker


@pytest.fixture
def m(requests_mock):
    return wrap_mock_register_uri(requests_mock)


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
    import tests.mock.login
    import tests.mock.oauth_claims
    import tests.mock.logout
    import tests.mock.panel
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

    m.post(jaraco.abode.helpers.urls.LOGIN, json=tests.mock.login.post_response_ok())
    m.get(
        jaraco.abode.helpers.urls.OAUTH_TOKEN,
        json=tests.mock.oauth_claims.get_response_ok(),
    )
    m.post(jaraco.abode.helpers.urls.LOGOUT, json=tests.mock.logout.post_response_ok())
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
