"""
Expose platform paths for the application.

>>> hasattr(paths, 'user_data')
True
"""

from __future__ import annotations

from collections.abc import Mapping

import pathlib
import platformdirs


class PlatformDirs(platformdirs.PlatformDirs):
    """
    Augment PlatformDirs to ensure the data path exists.

    >>> dirs = PlatformDirs(appname='Abode', appauthor=False)
    >>> dirs.override(data_path=getfixture('tmp_path') / 'data' / 'dir')
    >>> assert dirs.user_data.is_dir()
    """

    @property
    def user_data(self):
        self.user_data_path.mkdir(parents=True, exist_ok=True)
        return self.user_data_path

    def override(self, **kwargs: Mapping[str, pathlib.Path]):
        """
        Override the default _path variable.

        >>> dirs = PlatformDirs(appname='Abode', appauthor=False)
        >>> dirs.override(user_data=pathlib.Path('/tmp/foo'))
        """
        for name, path in kwargs.items():
            vars(self).update({name + '_path': path})


paths = PlatformDirs(appname='Abode', appauthor=False)
