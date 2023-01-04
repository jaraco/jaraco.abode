import platformdirs


class PlatformDirs(platformdirs.PlatformDirs):  # type: ignore
    @property
    def user_data(self):
        self.user_data_path.mkdir(exist_ok=True)
        return self.user_data_path


paths = PlatformDirs(appname='Abode', appauthor=False)
