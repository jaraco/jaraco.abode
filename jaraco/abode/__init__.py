"""
An Abode alarm Python library.
"""

import jaraco
from .devices.binary_sensor import BinarySensor
from .devices.camera import Camera
from .devices.cover import Cover
from .devices.light import Light
from .devices.lock import Lock
from .devices.switch import Switch
from .devices.sensor import Sensor
from .devices.valve import Valve
from .helpers import constants as CONST
from .helpers import errors as ERROR
from .client import Client
from .exceptions import Exception, AuthenticationException

__all__ = ['Exception', 'Client', 'AuthenticationException']


def _new_sensor(device_json, client):
    statuses = device_json.get(CONST.STATUSES_KEY, {})

    if any(key in statuses for key in CONST.SENSOR_KEYS):
        device_json['generic_type'] = CONST.TYPE_SENSOR
        return Sensor(device_json, client)

    version = device_json.get('version', '')

    device_json['generic_type'] = (
        CONST.TYPE_OCCUPANCY if version.startswith('MINIPIR') else CONST.TYPE_MOTION
    )

    return BinarySensor(device_json, client)


def new_device(device_json, client):
    """Create new device object for the given type."""
    try:
        type_tag = device_json['type_tag']
    except KeyError as exc:
        raise jaraco.abode.Exception(ERROR.UNABLE_TO_MAP_DEVICE) from exc

    generic_type = CONST.get_generic_type(type_tag.lower())
    device_json['generic_type'] = generic_type
    sensors = {
        CONST.TYPE_CONNECTIVITY: BinarySensor,
        CONST.TYPE_MOISTURE: BinarySensor,
        CONST.TYPE_OPENING: BinarySensor,
        CONST.TYPE_CAMERA: Camera,
        CONST.TYPE_COVER: Cover,
        CONST.TYPE_LIGHT: Light,
        CONST.TYPE_LOCK: Lock,
        CONST.TYPE_SWITCH: Switch,
        CONST.TYPE_VALVE: Valve,
        CONST.TYPE_UNKNOWN_SENSOR: _new_sensor,
    }
    sensor = sensors.get(generic_type, lambda *args: None)
    return sensor(device_json, client)
