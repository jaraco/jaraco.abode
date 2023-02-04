import types

import jaraco.abode
from .helpers import urls
from .helpers import errors as ERROR


CAMERA_RESOLUTION = 'ircamera_resolution_t'
CAMERA_GRAYSCALE = 'ircamera_gray_t'
SILENCE_SOUNDS = 'beeper_mute'

PANEL_SETTINGS = [
    CAMERA_RESOLUTION,
    CAMERA_GRAYSCALE,
    SILENCE_SOUNDS,
]

ENTRY_DELAY_AWAY = 'away_entry_delay'
EXIT_DELAY_AWAY = 'away_exit_delay'
ENTRY_DELAY_HOME = 'home_entry_delay'
EXIT_DELAY_HOME = 'home_exit_delay'

AREA_SETTINGS = [
    ENTRY_DELAY_AWAY,
    EXIT_DELAY_AWAY,
    ENTRY_DELAY_HOME,
    EXIT_DELAY_HOME,
]

DOOR_CHIME = 'door_chime'
WARNING_BEEP = 'warning_beep'
ENTRY_BEEP_AWAY = 'entry_beep_away'
EXIT_BEEP_AWAY = 'exit_beep_away'
ENTRY_BEEP_HOME = 'entry_beep_home'
EXIT_BEEP_HOME = 'exit_beep_home'
CONFIRM_SOUND = 'confirm_snd'
ALARM_LENGTH = 'alarm_len'
FINAL_BEEPS = 'final_beep'

SOUND_SETTINGS = [
    DOOR_CHIME,
    WARNING_BEEP,
    ENTRY_BEEP_AWAY,
    EXIT_BEEP_AWAY,
    ENTRY_BEEP_HOME,
    EXIT_BEEP_HOME,
    CONFIRM_SOUND,
    ALARM_LENGTH,
    FINAL_BEEPS,
]

SIREN_ENTRY_EXIT_SOUNDS = "entry"
SIREN_TAMPER_SOUNDS = "tamper"
SIREN_CONFIRM_SOUNDS = "confirm"

SIREN_SETTINGS = [
    SIREN_ENTRY_EXIT_SOUNDS,
    SIREN_TAMPER_SOUNDS,
    SIREN_CONFIRM_SOUNDS,
]


CAMERA_RES_320_240 = '0'
CAMERA_RES_640_480 = '2'

ALL_CAMERA_RES = [CAMERA_RES_320_240, CAMERA_RES_640_480]

DISABLE = '0'
ENABLE = '1'

DISABLE_ENABLE = [DISABLE, ENABLE]

ENTRY_EXIT_DELAY_DISABLE = '0'
ENTRY_EXIT_DELAY_10SEC = '10'
ENTRY_EXIT_DELAY_20SEC = '20'
ENTRY_EXIT_DELAY_30SEC = '30'
ENTRY_EXIT_DELAY_1MIN = '60'
ENTRY_EXIT_DELAY_2MIN = '120'
ENTRY_EXIT_DELAY_3MIN = '180'
ENTRY_EXIT_DELAY_4MIN = '240'

ALL_ENTRY_EXIT_DELAY = [
    ENTRY_EXIT_DELAY_DISABLE,
    ENTRY_EXIT_DELAY_10SEC,
    ENTRY_EXIT_DELAY_20SEC,
    ENTRY_EXIT_DELAY_30SEC,
    ENTRY_EXIT_DELAY_1MIN,
    ENTRY_EXIT_DELAY_2MIN,
    ENTRY_EXIT_DELAY_3MIN,
    ENTRY_EXIT_DELAY_4MIN,
]

VALID_SETTING_EXIT_AWAY = [
    ENTRY_EXIT_DELAY_30SEC,
    ENTRY_EXIT_DELAY_1MIN,
    ENTRY_EXIT_DELAY_2MIN,
    ENTRY_EXIT_DELAY_3MIN,
    ENTRY_EXIT_DELAY_4MIN,
]

SOUND_OFF = 'none'
SOUND_LOW = 'normal'
SOUND_HIGH = 'loud'

ALL_SOUND = [SOUND_OFF, SOUND_LOW, SOUND_HIGH]

VALID_SOUND_SETTINGS = [
    DOOR_CHIME,
    WARNING_BEEP,
    ENTRY_BEEP_AWAY,
    EXIT_BEEP_AWAY,
    ENTRY_BEEP_HOME,
    EXIT_BEEP_HOME,
    CONFIRM_SOUND,
]

ALARM_LENGTH_DISABLE = '0'
ALARM_LENGTH_1MIN = '60'
ALARM_LENGTH_2MIN = '120'
ALARM_LENGTH_3MIN = '180'
ALARM_LENGTH_4MIN = '240'
ALARM_LENGTH_5MIN = '300'
ALARM_LENGTH_6MIN = '360'
ALARM_LENGTH_7MIN = '420'
ALARM_LENGTH_8MIN = '480'
ALARM_LENGTH_9MIN = '540'
ALARM_LENGTH_10MIN = '600'
ALARM_LENGTH_11MIN = '660'
ALARM_LENGTH_12MIN = '720'
ALARM_LENGTH_13MIN = '780'
ALARM_LENGTH_14MIN = '840'
ALARM_LENGTH_15MIN = '900'

ALL_ALARM_LENGTH = [
    ALARM_LENGTH_DISABLE,
    ALARM_LENGTH_1MIN,
    ALARM_LENGTH_2MIN,
    ALARM_LENGTH_3MIN,
    ALARM_LENGTH_4MIN,
    ALARM_LENGTH_5MIN,
    ALARM_LENGTH_6MIN,
    ALARM_LENGTH_7MIN,
    ALARM_LENGTH_8MIN,
    ALARM_LENGTH_9MIN,
    ALARM_LENGTH_10MIN,
    ALARM_LENGTH_11MIN,
    ALARM_LENGTH_12MIN,
    ALARM_LENGTH_13MIN,
    ALARM_LENGTH_14MIN,
    ALARM_LENGTH_15MIN,
]

FINAL_BEEPS_DISABLE = '0'
FINAL_BEEPS_3SEC = '3'
FINAL_BEEPS_4SEC = '4'
FINAL_BEEPS_5SEC = '5'
FINAL_BEEPS_6SEC = '6'
FINAL_BEEPS_7SEC = '7'
FINAL_BEEPS_8SEC = '8'
FINAL_BEEPS_9SEC = '9'
FINAL_BEEPS_10SEC = '10'

ALL_FINAL_BEEPS = [
    FINAL_BEEPS_DISABLE,
    FINAL_BEEPS_3SEC,
    FINAL_BEEPS_4SEC,
    FINAL_BEEPS_5SEC,
    FINAL_BEEPS_6SEC,
    FINAL_BEEPS_7SEC,
    FINAL_BEEPS_8SEC,
    FINAL_BEEPS_9SEC,
    FINAL_BEEPS_10SEC,
]


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
    names = PANEL_SETTINGS
    path = urls.SETTINGS

    def validate(self):
        if self.name == CAMERA_RESOLUTION and self.value not in ALL_CAMERA_RES:
            raise jaraco.abode.Exception(ERROR.INVALID_SETTING_VALUE)
        if (
            self.name in [CAMERA_GRAYSCALE, SILENCE_SOUNDS]
            and self.value not in DISABLE_ENABLE
        ):
            raise jaraco.abode.Exception(ERROR.INVALID_SETTING_VALUE)

    @property
    def data(self):
        return {self.name: self.value}


class Area(Setting):
    names = AREA_SETTINGS
    path = urls.AREAS

    def validate(self):
        # Exit delay has some specific limitations
        if self.name == EXIT_DELAY_AWAY and self.value not in VALID_SETTING_EXIT_AWAY:
            raise jaraco.abode.Exception(ERROR.INVALID_SETTING_VALUE)
        if self.value not in ALL_ENTRY_EXIT_DELAY:
            raise jaraco.abode.Exception(ERROR.INVALID_SETTING_VALUE)

    @property
    def data(self):
        return {'area': self.area, self.name: self.value}


class Sound(Setting):
    names = SOUND_SETTINGS
    path = urls.SOUNDS

    def validate(self):
        if self.name in VALID_SOUND_SETTINGS and self.value not in ALL_SOUND:
            raise jaraco.abode.Exception(ERROR.INVALID_SETTING_VALUE)
        if self.name == ALARM_LENGTH and self.value not in ALL_ALARM_LENGTH:
            raise jaraco.abode.Exception(ERROR.INVALID_SETTING_VALUE)
        if self.name == FINAL_BEEPS and self.value not in ALL_FINAL_BEEPS:
            raise jaraco.abode.Exception(ERROR.INVALID_SETTING_VALUE)

    @property
    def data(self):
        return {'area': self.area, self.name: self.value}


class Siren(Setting):
    names = SIREN_SETTINGS
    path = urls.SIREN

    def validate(self):
        if self.value not in DISABLE_ENABLE:
            raise jaraco.abode.Exception(ERROR.INVALID_SETTING_VALUE)

    @property
    def data(self):
        return {'action': self.name, 'option': self.value}
