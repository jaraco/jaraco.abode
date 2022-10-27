"""Test the Abode device classes."""
import json

import pytest

import jaraco.abode
from jaraco.abode.devices import AbodeDevice
from jaraco.abode.devices.alarm import AbodeAlarm
from jaraco.abode.devices.binary_sensor import AbodeBinarySensor
from jaraco.abode.devices.cover import AbodeCover
from jaraco.abode.devices.light import AbodeLight
from jaraco.abode.devices.lock import AbodeLock
from jaraco.abode.devices.switch import AbodeSwitch
import jaraco.abode.helpers.constants as CONST
from .mock import devices as DEVICES
from .mock.devices import door_contact as DOOR_CONTACT
from .mock.devices import door_lock as DOOR_LOCK
from .mock.devices import glass as GLASS
from .mock.devices import ir_camera as IR_CAMERA
from .mock.devices import keypad as KEYPAD
from .mock.devices import pir as PIR
from .mock.devices import power_switch_meter as POWERMETER
from .mock.devices import power_switch_sensor as POWERSENSOR
from .mock.devices import remote_controller as REMOTE_CONTROLLER
from .mock.devices import secure_barrier as SECUREBARRIER
from .mock.devices import siren as SIREN
from .mock.devices import status_display as STATUS_DISPLAY
from .mock.devices import water_sensor as WATER_SENSOR
from .mock.devices import unknown as UNKNOWN
from .mock import login as LOGIN
from .mock import oauth_claims as OAUTH_CLAIMS
from .mock import logout as LOGOUT
from .mock import panel as PANEL


class TestDevice:
    """Test the generic device class."""

    def tests_device_mapping_typetag(self):
        """Check the generic Abode device maps to none without typetag."""
        # Set up device
        device_text = GLASS.device(
            status=CONST.STATUS_ONLINE,
            low_battery=True,
            no_response=True,
            tampered=True,
            out_of_order=True,
        )

        device_json = json.loads(device_text)

        with pytest.raises(jaraco.abode.AbodeException):
            device_json['type_tag'] = ""
            jaraco.abode.new_device(device_json, self.abode)

        with pytest.raises(jaraco.abode.AbodeException):
            device_json['type_tag'] = None
            jaraco.abode.new_device(device_json, self.abode)

        with pytest.raises(jaraco.abode.AbodeException):
            del device_json['type_tag']
            jaraco.abode.new_device(device_json, self.abode)

    def tests_device_auto_naming(self):
        """Check the generic Abode device creates a name."""
        # Set up device
        device_text = GLASS.device(
            status=CONST.STATUS_ONLINE,
            low_battery=True,
            no_response=True,
            tampered=True,
            out_of_order=True,
        )

        device_json = json.loads(device_text)

        device_json['name'] = ""
        device = jaraco.abode.new_device(device_json, self.abode)
        generated_name = device.type + ' ' + device.device_id
        assert device.name == generated_name

        device_json['name'] = None
        device = jaraco.abode.new_device(device_json, self.abode)
        generated_name = device.type + ' ' + device.device_id
        assert device.name == generated_name

        del device_json['name']
        device = jaraco.abode.new_device(device_json, self.abode)
        generated_name = device.type + ' ' + device.device_id
        assert device.name == generated_name

    def tests_device_init(self, m):
        """Check the generic Abode device class init's properly."""
        # Set up URLs
        m.post(CONST.LOGIN_URL, text=LOGIN.post_response_ok())
        m.get(CONST.OAUTH_TOKEN_URL, text=OAUTH_CLAIMS.get_response_ok())
        m.post(CONST.LOGOUT_URL, text=LOGOUT.post_response_ok())
        m.get(CONST.PANEL_URL, text=PANEL.get_response_ok())

        # Set up device
        device_text = (
            '['
            + GLASS.device(
                status=CONST.STATUS_ONLINE,
                low_battery=True,
                no_response=True,
                tampered=True,
                out_of_order=True,
                uuid='testuuid00000001',
            )
            + ']'
        )
        device_json = json.loads(device_text)

        m.get(CONST.DEVICES_URL, text=device_text)

        # Logout to reset everything
        self.abode.logout()

        # Get our specific device
        device = self.abode.get_device(GLASS.DEVICE_ID)

        # Check device states match
        assert device is not None

        assert device.name == device_json[0]['name']
        assert device.type == device_json[0]['type']
        assert device.type_tag == device_json[0]['type_tag']
        assert device.device_id == device_json[0]['id']
        assert device.device_uuid == device_json[0]['uuid']
        assert device.status == CONST.STATUS_ONLINE
        assert device.battery_low
        assert device.no_response
        assert device.tampered
        assert device.out_of_order
        assert device.desc is not None

    def tests_generic_device_refresh(self, m):
        """Check the generic Abode device class init's properly."""
        # Set up URL's
        m.post(CONST.LOGIN_URL, text=LOGIN.post_response_ok())
        m.get(CONST.OAUTH_TOKEN_URL, text=OAUTH_CLAIMS.get_response_ok())
        m.post(CONST.LOGOUT_URL, text=LOGOUT.post_response_ok())
        m.get(CONST.PANEL_URL, text=PANEL.get_response_ok())

        # Set up online device
        device_text_online = '[' + GLASS.device(status=CONST.STATUS_ONLINE) + ']'
        m.get(CONST.DEVICES_URL, text=device_text_online)

        # Set up offline device
        device_text_offline = '[' + GLASS.device(status=CONST.STATUS_OFFLINE) + ']'
        device_url = CONST.DEVICE_URL.format(device_id=GLASS.DEVICE_ID)
        m.get(device_url, text=device_text_offline)

        # Logout to reset everything
        self.abode.logout()

        # Get the first device and test
        device = self.abode.get_device(GLASS.DEVICE_ID)
        assert device.status == CONST.STATUS_ONLINE

        # Refresh the device and test
        device = self.abode.get_device(GLASS.DEVICE_ID, refresh=True)
        assert device.status == CONST.STATUS_OFFLINE

    def tests_multiple_devices(self, m):
        """Tests that multiple devices are returned properly."""
        # Set up URL's
        m.post(CONST.LOGIN_URL, text=LOGIN.post_response_ok())
        m.get(CONST.OAUTH_TOKEN_URL, text=OAUTH_CLAIMS.get_response_ok())
        m.post(CONST.LOGOUT_URL, text=LOGOUT.post_response_ok())
        m.get(CONST.PANEL_URL, text=PANEL.get_response_ok(mode=CONST.MODE_STANDBY))

        # Set up a list of devices
        dev_list = (
            '['
            + POWERSENSOR.device()
            + ","
            + DOOR_CONTACT.device()
            + ","
            + GLASS.device()
            + ']'
        )

        m.get(CONST.DEVICES_URL, text=dev_list)

        # Logout to reset everything
        self.abode.logout()

        # Get our devices
        devices = self.abode.get_devices()

        # Assert four devices - three from above + 1 alarm
        assert devices is not None
        assert len(devices) == 4

        # Get each individual device by device ID
        psd = self.abode.get_device(POWERSENSOR.DEVICE_ID)
        assert psd is not None

        # Get each individual device by device ID
        psd = self.abode.get_device(DOOR_CONTACT.DEVICE_ID)
        assert psd is not None

        # Get each individual device by device ID
        psd = self.abode.get_device(GLASS.DEVICE_ID)
        assert psd is not None

    def tests_unknown_devices(self, m):
        """Tests that multiple devices are returned properly."""
        # Set up URL's
        m.post(CONST.LOGIN_URL, text=LOGIN.post_response_ok())
        m.get(CONST.OAUTH_TOKEN_URL, text=OAUTH_CLAIMS.get_response_ok())
        m.post(CONST.LOGOUT_URL, text=LOGOUT.post_response_ok())
        m.get(CONST.PANEL_URL, text=PANEL.get_response_ok(mode=CONST.MODE_STANDBY))

        # Set up a list of devices
        dev_list = '[' + UNKNOWN.device() + ']'

        m.get(CONST.DEVICES_URL, text=dev_list)

        # Logout to reset everything
        self.abode.logout()

        # Get our devices
        devices = self.abode.get_devices()

        # Assert 1 device - skipped device above + 1 alarm
        assert devices is not None
        assert len(devices) == 1

    def tests_device_category_filter(self, m):
        """Tests that device category filter returns requested results."""
        # Set up URL's
        m.post(CONST.LOGIN_URL, text=LOGIN.post_response_ok())
        m.get(CONST.OAUTH_TOKEN_URL, text=OAUTH_CLAIMS.get_response_ok())
        m.post(CONST.LOGOUT_URL, text=LOGOUT.post_response_ok())
        m.get(CONST.PANEL_URL, text=PANEL.get_response_ok(mode=CONST.MODE_STANDBY))

        # Set up a list of devices
        dev_list = (
            '['
            + POWERSENSOR.device(
                devid='ps1',
                status=CONST.STATUS_OFF,
                low_battery=False,
                no_response=False,
            )
            + ","
            + POWERSENSOR.device(
                devid='ps2',
                status=CONST.STATUS_OFF,
                low_battery=False,
                no_response=False,
            )
            + ","
            + GLASS.device(
                devid='gb1',
                status=CONST.STATUS_OFF,
                low_battery=False,
                no_response=False,
            )
            + ']'
        )

        m.get(CONST.DEVICES_URL, text=dev_list)

        # Logout to reset everything
        self.abode.logout()

        # Get our glass devices
        devices = self.abode.get_devices(generic_type=CONST.TYPE_CONNECTIVITY)

        assert devices is not None
        assert len(devices) == 1

        # Get our power switch devices
        devices = self.abode.get_devices(generic_type=CONST.TYPE_SWITCH)

        assert devices is not None
        assert len(devices) == 2

    def tests_no_control_url(self, m):
        """Check that devices return false without control url's."""
        # Set up URL's
        m.post(CONST.LOGIN_URL, text=LOGIN.post_response_ok())
        m.get(CONST.OAUTH_TOKEN_URL, text=OAUTH_CLAIMS.get_response_ok())
        m.post(CONST.LOGOUT_URL, text=LOGOUT.post_response_ok())
        m.get(CONST.PANEL_URL, text=PANEL.get_response_ok())

        m.get(CONST.DEVICES_URL, text=GLASS.device(status=CONST.STATUS_ONLINE))

        # Logout to reset everything
        self.abode.logout()

        # Get device
        device = self.abode.get_device(GLASS.DEVICE_ID)

        assert device is not None
        assert not device.set_status('1')
        assert not device.set_level('99')

    def tests_device_status_changes(self, m):
        """Tests that device status changes work as expected."""
        # Set up URL's
        m.post(CONST.LOGIN_URL, text=LOGIN.post_response_ok())
        m.get(CONST.OAUTH_TOKEN_URL, text=OAUTH_CLAIMS.get_response_ok())
        m.post(CONST.LOGOUT_URL, text=LOGOUT.post_response_ok())
        m.get(CONST.PANEL_URL, text=PANEL.get_response_ok(mode=CONST.MODE_STANDBY))
        m.get(
            CONST.DEVICES_URL,
            text=POWERSENSOR.device(
                devid=POWERSENSOR.DEVICE_ID,
                status=CONST.STATUS_OFF,
                low_battery=False,
                no_response=False,
            ),
        )

        # Logout to reset everything
        self.abode.logout()

        # Get our power switch
        device = self.abode.get_device(POWERSENSOR.DEVICE_ID)

        # Test that we have our device
        assert device is not None
        assert device.status == CONST.STATUS_OFF
        assert not device.is_on

        # Set up control url response
        control_url = POWERSENSOR.CONTROL_URL
        m.put(
            control_url,
            text=DEVICES.status_put_response_ok(
                devid=POWERSENSOR.DEVICE_ID, status=CONST.STATUS_ON_INT
            ),
        )

        # Change the mode to "on"
        assert device.switch_on()
        assert device.status == CONST.STATUS_ON
        assert device.is_on

        # Change response
        m.put(
            control_url,
            text=DEVICES.status_put_response_ok(
                devid=POWERSENSOR.DEVICE_ID, status=CONST.STATUS_OFF_INT
            ),
        )

        # Change the mode to "off"
        assert device.switch_off()
        assert device.status == CONST.STATUS_OFF
        assert not device.is_on

        # Test that an invalid device ID in response throws exception
        m.put(
            control_url,
            text=DEVICES.status_put_response_ok(
                devid='ZW:deadbeef', status=CONST.STATUS_OFF_INT
            ),
        )

        with pytest.raises(jaraco.abode.AbodeException):
            device.switch_on()

        # Test that an invalid status in response throws exception
        m.put(
            control_url,
            text=DEVICES.status_put_response_ok(
                devid=POWERSENSOR.DEVICE_ID, status=CONST.STATUS_OFF_INT
            ),
        )

        with pytest.raises(jaraco.abode.AbodeException):
            device.switch_on()

    def tests_device_level_changes(self, m):
        """Tests that device level changes work as expected."""
        # Set up URL's
        m.post(CONST.LOGIN_URL, text=LOGIN.post_response_ok())
        m.get(CONST.OAUTH_TOKEN_URL, text=OAUTH_CLAIMS.get_response_ok())
        m.post(CONST.LOGOUT_URL, text=LOGOUT.post_response_ok())
        m.get(CONST.PANEL_URL, text=PANEL.get_response_ok(mode=CONST.MODE_STANDBY))

        # TODO: Test with a device that supports levels
        m.get(
            CONST.DEVICES_URL,
            text=POWERSENSOR.device(
                devid=POWERSENSOR.DEVICE_ID,
                status=CONST.STATUS_OFF,
                low_battery=False,
                no_response=False,
            ),
        )

        # Logout to reset everything
        self.abode.logout()

        # Get our power switch
        device = self.abode.get_device(POWERSENSOR.DEVICE_ID)

        # Test that we have our device
        assert device is not None
        assert device.status == CONST.STATUS_OFF
        assert not device.is_on

        # Set up control url response
        m.put(
            POWERSENSOR.CONTROL_URL,
            text=DEVICES.level_put_response_ok(
                devid=POWERSENSOR.DEVICE_ID, level='100'
            ),
        )

        # Change the level to int 100
        assert device.set_level(100)
        # self.assertEqual(device.level, '100')

        # Change response
        m.put(
            POWERSENSOR.CONTROL_URL,
            text=DEVICES.level_put_response_ok(devid=POWERSENSOR.DEVICE_ID, level='25'),
        )

        # Change the level to str '25'
        assert device.set_level('25')
        # self.assertEqual(device.level, '25')

        # Test that an invalid device ID in response throws exception
        m.put(
            POWERSENSOR.CONTROL_URL,
            text=DEVICES.level_put_response_ok(devid='ZW:deadbeef', level='25'),
        )

        with pytest.raises(jaraco.abode.AbodeException):
            device.set_level(25)

        # Test that an invalid level in response throws exception
        m.put(
            POWERSENSOR.CONTROL_URL,
            text=DEVICES.level_put_response_ok(devid=POWERSENSOR.DEVICE_ID, level='98'),
        )

        with pytest.raises(jaraco.abode.AbodeException):
            device.set_level('28')

    def tests_all_devices(self, m):
        """Tests that all mocked devices are mapped correctly."""
        # Set up URL's
        m.post(CONST.LOGIN_URL, text=LOGIN.post_response_ok())
        m.get(CONST.OAUTH_TOKEN_URL, text=OAUTH_CLAIMS.get_response_ok())
        m.post(CONST.LOGOUT_URL, text=LOGOUT.post_response_ok())
        m.get(CONST.PANEL_URL, text=PANEL.get_response_ok(mode=CONST.MODE_STANDBY))

        # Create all devices
        all_devices = (
            '['
            + DOOR_CONTACT.device()
            + ','
            + DOOR_LOCK.device()
            + ','
            + GLASS.device()
            + ','
            + IR_CAMERA.device()
            + ','
            + KEYPAD.device()
            + ','
            + PIR.device()
            + ','
            + POWERMETER.device()
            + ','
            + POWERSENSOR.device()
            + ','
            + REMOTE_CONTROLLER.device()
            + ','
            + SECUREBARRIER.device()
            + ','
            + SIREN.device()
            + ','
            + STATUS_DISPLAY.device()
            + ','
            + WATER_SENSOR.device()
            + ']'
        )

        m.get(CONST.DEVICES_URL, text=all_devices)

        # Logout to reset everything
        self.abode.logout()

        # Loop through all devices
        for device in self.abode.get_devices():
            class_type = {
                # Alarm
                CONST.TYPE_ALARM: AbodeAlarm,
                # Binary Sensors
                CONST.TYPE_CONNECTIVITY: AbodeBinarySensor,
                CONST.TYPE_MOISTURE: AbodeBinarySensor,
                CONST.TYPE_OPENING: AbodeBinarySensor,
                CONST.TYPE_MOTION: AbodeBinarySensor,
                CONST.TYPE_OCCUPANCY: AbodeBinarySensor,
                # Camera
                CONST.TYPE_CAMERA: AbodeDevice,
                # Cover
                CONST.TYPE_COVER: AbodeCover,
                # Dimmer
                CONST.TYPE_LIGHT: AbodeLight,
                # Lock
                CONST.TYPE_LOCK: AbodeLock,
                # Switch
                CONST.TYPE_SWITCH: AbodeSwitch,
            }.get(device.generic_type)

            assert class_type is not None, device.type + ' is not mapped.'
            assert isinstance(device, class_type), (
                device.type
                + ' is of class '
                + str(device.__class__.__name__)
                + ' but mapped to '
                + str(class_type.__name__)
            )
