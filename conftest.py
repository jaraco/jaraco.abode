import pytest
import jaraco.abode


collect_ignore = ['abodepy']


@pytest.fixture(autouse=True)
def abode_instance(request):
    if request.instance is None:
        return

    request.instance.abode = jaraco.abode.Abode(
        username='foobar', password='deadbeef', disable_cache=True
    )


@pytest.fixture
def m(requests_mock):
    return requests_mock
