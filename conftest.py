import urllib.parse

import pytest
import jaraco.abode


@pytest.fixture(autouse=True)
def instance_client(request):
    if request.instance is None:
        return

    request.instance.client = jaraco.abode.Client(
        username='foobar', password='deadbeef', disable_cache=True
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
