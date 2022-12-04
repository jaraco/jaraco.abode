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

# GENERIC ABODE DEVICE TYPES
TYPE_ALARM = "alarm"
TYPE_CAMERA = "camera"
TYPE_CONNECTIVITY = "connectivity"
TYPE_COVER = "cover"
TYPE_LIGHT = "light"
TYPE_LOCK = "lock"
TYPE_MOISTURE = "moisture"
TYPE_MOTION = "motion"
TYPE_OCCUPANCY = "occupancy"
TYPE_OPENING = "door"
TYPE_SENSOR = "sensor"
TYPE_SWITCH = "switch"
TYPE_VALVE = "valve"

TYPE_UNKNOWN_SENSOR = "unknown_sensor"

BINARY_SENSOR_TYPES = [
    TYPE_CONNECTIVITY,
    TYPE_MOISTURE,
    TYPE_MOTION,
    TYPE_OCCUPANCY,
    TYPE_OPENING,
]

# DEVICE TYPE_TAGS
# Alarm
DEVICE_ALARM = 'device_type.alarm'

# Binary Sensors - Connectivity
DEVICE_GLASS_BREAK = 'device_type.glass'
DEVICE_KEYPAD = 'device_type.keypad'
DEVICE_REMOTE_CONTROLLER = 'device_type.remote_controller'
DEVICE_SIREN = 'device_type.siren'
DEVICE_STATUS_DISPLAY = 'device_type.bx'

# Binary Sensors - Opening
DEVICE_DOOR_CONTACT = 'device_type.door_contact'

# Cameras
DEVICE_MOTION_CAMERA = 'device_type.ir_camera'
DEVICE_MOTION_VIDEO_CAMERA = 'device_type.ir_camcoder'
DEVICE_IP_CAM = 'device_type.ipcam'
DEVICE_OUTDOOR_MOTION_CAMERA = 'device_type.out_view'
DEVICE_OUTDOOR_SMART_CAMERA = 'device_type.vdp'
DEVICE_MINI_CAM = 'device_type.mini_cam'

# Covers
DEVICE_SECURE_BARRIER = 'device_type.secure_barrier'

# Dimmers
DEVICE_DIMMER = 'device_type.dimmer'
DEVICE_DIMMER_METER = 'device_type.dimmer_meter'
DEVICE_HUE = 'device_type.hue'

# Locks
DEVICE_DOOR_LOCK = 'device_type.door_lock'

# Moisture
DEVICE_WATER_SENSOR = 'device_type.water_sensor'

# Switches
DEVICE_SWITCH = 'device_type.switch'
DEVICE_NIGHT_SWITCH = 'device_type.night_switch'
DEVICE_POWER_SWITCH_SENSOR = 'device_type.power_switch_sensor'
DEVICE_POWER_SWITCH_METER = 'device_type.power_switch_meter'

# Water Valve
DEVICE_VALVE = 'device_type.valve'

# Unknown Sensor
# These device types are all considered 'occupancy' but could apparently
# also be multi-sensors based on their json.
DEVICE_ROOM_SENSOR = 'device_type.room_sensor'
DEVICE_TEMPERATURE_SENSOR = 'device_type.temperature_sensor'
DEVICE_MULTI_SENSOR = 'device_type.lm'  # LM = LIGHT MOTION?
DEVICE_PIR = 'device_type.pir'  # Passive Infrared Occupancy?
DEVICE_POVS = 'device_type.povs'

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
    DEVICE_ALARM: TYPE_ALARM,
    # Binary Sensors - Connectivity
    DEVICE_GLASS_BREAK: TYPE_CONNECTIVITY,
    DEVICE_KEYPAD: TYPE_CONNECTIVITY,
    DEVICE_REMOTE_CONTROLLER: TYPE_CONNECTIVITY,
    DEVICE_SIREN: TYPE_CONNECTIVITY,
    DEVICE_STATUS_DISPLAY: TYPE_CONNECTIVITY,
    # Binary Sensors - Opening
    DEVICE_DOOR_CONTACT: TYPE_OPENING,
    # Cameras
    DEVICE_MOTION_CAMERA: TYPE_CAMERA,
    DEVICE_MOTION_VIDEO_CAMERA: TYPE_CAMERA,
    DEVICE_IP_CAM: TYPE_CAMERA,
    DEVICE_OUTDOOR_MOTION_CAMERA: TYPE_CAMERA,
    DEVICE_OUTDOOR_SMART_CAMERA: TYPE_CAMERA,
    DEVICE_MINI_CAM: TYPE_CAMERA,
    # Covers
    DEVICE_SECURE_BARRIER: TYPE_COVER,
    # Lights (Dimmers)
    DEVICE_DIMMER: TYPE_LIGHT,
    DEVICE_DIMMER_METER: TYPE_LIGHT,
    DEVICE_HUE: TYPE_LIGHT,
    # Locks
    DEVICE_DOOR_LOCK: TYPE_LOCK,
    # Moisture
    DEVICE_WATER_SENSOR: TYPE_CONNECTIVITY,
    # Switches
    DEVICE_SWITCH: TYPE_SWITCH,
    DEVICE_NIGHT_SWITCH: TYPE_SWITCH,
    DEVICE_POWER_SWITCH_SENSOR: TYPE_SWITCH,
    DEVICE_POWER_SWITCH_METER: TYPE_SWITCH,
    # Water Valve
    DEVICE_VALVE: TYPE_VALVE,
    # Unknown Sensors
    # More data needed to determine type
    DEVICE_ROOM_SENSOR: TYPE_UNKNOWN_SENSOR,
    DEVICE_TEMPERATURE_SENSOR: TYPE_UNKNOWN_SENSOR,
    DEVICE_MULTI_SENSOR: TYPE_UNKNOWN_SENSOR,
    DEVICE_PIR: TYPE_UNKNOWN_SENSOR,
    DEVICE_POVS: TYPE_UNKNOWN_SENSOR,
}


def get_generic_type(type_tag):
    """Map type tag to generic type."""
    return type_map.get(type_tag.lower())
