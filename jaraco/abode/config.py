import platformdirs


class PlatformDirs(platformdirs.PlatformDirs):  # type: ignore
    """
    >>> dirs = PlatformDirs(appname='Abode', appauthor=False)
    >>> alt_udp = getfixture('tmp_path') / 'data' / 'dir'
    >>> vars(dirs).update(user_data_path=alt_udp)
    >>> assert dirs.user_data.is_dir()
    """

    @property
    def user_data(self):
        self.user_data_path.mkdir(parents=True, exist_ok=True)
        return self.user_data_path


paths = PlatformDirs(appname='Abode', appauthor=False)
