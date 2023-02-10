# NOTIFICATION CONSTANTS
SOCKETIO_URL = 'wss://my.goabode.com/socket.io/'

SOCKETIO_HEADERS = {
    'Origin': 'https://my.goabode.com/',
}

# DICTIONARIES
MODE_STANDBY = 'standby'
MODE_HOME = 'home'
MODE_AWAY = 'away'

ALL_MODES = [MODE_STANDBY, MODE_HOME, MODE_AWAY]

ALL_MODES_STR = ", ".join(ALL_MODES)

ARMED = dict(home=True, away=True, standby=False)

STATUS_ONLINE = 'Online'
STATUS_OFFLINE = 'Offline'

STATUS_OPEN = 'Open'
STATUS_OPEN_INT = 1
STATUS_CLOSED = 'Closed'
STATUS_CLOSED_INT = 0

STATUS_LOCKOPEN = 'LockOpen'
STATUS_LOCKOPEN_INT = 0
STATUS_LOCKCLOSED = 'LockClosed'
STATUS_LOCKCLOSED_INT = 1

STATUS_ON = 'On'
STATUS_ON_INT = 1
STATUS_OFF = 'Off'
STATUS_OFF_INT = 0

COLOR_MODE_ON = 0
COLOR_MODE_OFF = 2

STATUSES_KEY = 'statuses'
TEMP_STATUS_KEY = 'temperature'
LUX_STATUS_KEY = 'lux'
HUMI_STATUS_KEY = 'humidity'
SENSOR_KEYS = [TEMP_STATUS_KEY, LUX_STATUS_KEY, HUMI_STATUS_KEY]

UNIT_CELSIUS = '°C'
UNIT_FAHRENHEIT = '°F'
UNIT_PERCENT = '%'
UNIT_LUX = 'lx'
LUX = 'lux'

BRIGHTNESS_KEY = 'statusEx'

type_map = {
    # Alarm
    'device_type.alarm': 'alarm',
    # Binary Sensors - Connectivity
    'device_type.glass': 'connectivity',
    'device_type.keypad': 'connectivity',
    'device_type.remote_controller': 'connectivity',
    'device_type.siren': 'connectivity',
    # status display
    'device_type.bx': 'connectivity',
    # Binary Sensors - Opening
    'device_type.door_contact': 'door',
    # Cameras
    # motion camera
    'device_type.ir_camera': 'camera',
    # motion video camera
    'device_type.ir_camcoder': 'camera',
    'device_type.ipcam': 'camera',
    # outdoor motion camera
    'device_type.out_view': 'camera',
    # outdoor smart camera
    'device_type.vdp': 'camera',
    'device_type.mini_cam': 'camera',
    # Covers
    'device_type.secure_barrier': 'cover',
    # Lights (Dimmers)
    'device_type.dimmer': 'light',
    'device_type.dimmer_meter': 'light',
    'device_type.hue': 'light',
    # Locks
    'device_type.door_lock': 'lock',
    # Moisture
    'device_type.water_sensor': 'connectivity',
    # Switches
    'device_type.switch': 'switch',
    'device_type.night_switch': 'switch',
    'device_type.power_switch_sensor': 'switch',
    'device_type.power_switch_meter': 'switch',
    # Water Valve
    'device_type.valve': 'valve',
    # Unknown Sensors
    # These device types are all considered 'occupancy' but could apparently
    # also be multi-sensors based on their state.
    'device_type.room_sensor': 'unknown',
    'device_type.temperature_sensor': 'unknown',
    # LM = LIGHT MOTION?
    'device_type.lm': 'unknown',
    'device_type.pir': 'unknown',
    'device_type.povs': 'unknown',
}


def get_generic_type(type_tag):
    """Map type tag to generic type."""
    return type_map.get(type_tag.lower())
