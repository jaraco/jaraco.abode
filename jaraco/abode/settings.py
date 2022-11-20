import types

import jaraco.abode
from .helpers import constants as CONST
from .helpers import errors as ERROR


class Setting(types.SimpleNamespace):
    @classmethod
    def load(cls, name, value, area):
        matches = (subcl for subcl in cls.__subclasses__() if name in subcl.names)
        try:
            (match,) = matches
        except ValueError:
            raise jaraco.abode.Exception(ERROR.INVALID_SETTING)

        ob = match(name=name, value=value, area=area)
        ob.validate()
        return ob


class Panel(Setting):
    names = CONST.PANEL_SETTINGS
    path = CONST.SETTINGS_URL

    def validate(self):
        if (
            self.name == CONST.SETTING_CAMERA_RESOLUTION
            and self.value not in CONST.SETTING_ALL_CAMERA_RES
        ):
            raise jaraco.abode.Exception(
                ERROR.INVALID_SETTING_VALUE, CONST.SETTING_ALL_CAMERA_RES
            )
        if (
            self.name in [CONST.SETTING_CAMERA_GRAYSCALE, CONST.SETTING_SILENCE_SOUNDS]
            and self.value not in CONST.SETTING_DISABLE_ENABLE
        ):
            raise jaraco.abode.Exception(
                ERROR.INVALID_SETTING_VALUE, CONST.SETTING_DISABLE_ENABLE
            )

    @property
    def data(self):
        return {self.name: self.value}


class Area(Setting):
    names = CONST.AREA_SETTINGS
    path = CONST.AREAS_URL

    def validate(self):
        # Exit delay has some specific limitations
        if (
            self.name == CONST.SETTING_EXIT_DELAY_AWAY
            and self.value not in CONST.VALID_SETTING_EXIT_AWAY
        ):
            raise jaraco.abode.Exception(
                ERROR.INVALID_SETTING_VALUE, CONST.VALID_SETTING_EXIT_AWAY
            )
        if self.value not in CONST.ALL_SETTING_ENTRY_EXIT_DELAY:
            raise jaraco.abode.Exception(
                ERROR.INVALID_SETTING_VALUE, CONST.ALL_SETTING_ENTRY_EXIT_DELAY
            )

    @property
    def data(self):
        return {'area': self.area, self.name: self.value}


class Sound(Setting):
    names = CONST.SOUND_SETTINGS
    path = CONST.SOUNDS_URL

    def validate(self):
        if (
            self.name in CONST.VALID_SOUND_SETTINGS
            and self.value not in CONST.ALL_SETTING_SOUND
        ):
            raise jaraco.abode.Exception(
                ERROR.INVALID_SETTING_VALUE, CONST.ALL_SETTING_SOUND
            )
        if (
            self.name == CONST.SETTING_ALARM_LENGTH
            and self.value not in CONST.ALL_SETTING_ALARM_LENGTH
        ):
            raise jaraco.abode.Exception(
                ERROR.INVALID_SETTING_VALUE, CONST.ALL_SETTING_ALARM_LENGTH
            )
        if (
            self.name == CONST.SETTING_FINAL_BEEPS
            and self.value not in CONST.ALL_SETTING_FINAL_BEEPS
        ):
            raise jaraco.abode.Exception(
                ERROR.INVALID_SETTING_VALUE, CONST.ALL_SETTING_FINAL_BEEPS
            )

    @property
    def data(self):
        return {'area': self.area, self.name: self.value}


class Siren(Setting):
    names = CONST.SIREN_SETTINGS
    path = CONST.SIREN_URL

    def validate(self):
        if self.value not in CONST.SETTING_DISABLE_ENABLE:
            raise jaraco.abode.Exception(
                ERROR.INVALID_SETTING_VALUE, CONST.SETTING_DISABLE_ENABLE
            )

    @property
    def data(self):
        return {'action': self.name, 'option': self.value}
