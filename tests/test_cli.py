import sys

import pytest

from jaraco.abode import cli


def test_cli(monkeypatch, capsys):
    monkeypatch.setattr(sys, 'argv', ['name', '--help'])
    with pytest.raises(SystemExit) as exc:
        cli.main()
    assert exc.value.code == 0
    assert 'usage' in capsys.readouterr().out
