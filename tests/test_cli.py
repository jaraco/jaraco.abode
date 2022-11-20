import sys
import unittest.mock

import pytest

from jaraco.abode import cli, client


@pytest.fixture
def mocked_client():
    return unittest.mock.create_autospec(client.Client)()


def test_cli(monkeypatch, capsys):
    monkeypatch.setattr(sys, 'argv', ['name', '--help'])
    with pytest.raises(SystemExit) as exc:
        cli.main()
    assert exc.value.code == 0
    assert 'usage' in capsys.readouterr().out


class TestDispatcher:
    def test_dispatch(self):
        args = cli.build_parser().parse_args([])
        dispatcher = cli.Dispatcher(mocked_client, args)
        dispatcher.dispatch()
