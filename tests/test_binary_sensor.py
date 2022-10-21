"""Test the Abode binary sensors."""
import functools
import itertools

import jaraco.abode.helpers.constants as CONST

import tests.mock.login as LOGIN
import tests.mock.oauth_claims as OAUTH_CLAIMS
import tests.mock.logout as LOGOUT
import tests.mock.panel as PANEL
import tests.mock.devices.door_contact as DOOR_CONTACT
import tests.mock.devices.glass as GLASS
import tests.mock.devices.keypad as KEYPAD
import tests.mock.devices.remote_controller as REMOTE_CONTROLLER
import tests.mock.devices.siren as SIREN
import tests.mock.devices.status_display as STATUS_DISPLAY
import tests.mock.devices.water_sensor as WATER_SENSOR


class TestBinarySensors:
    """Test the AbodePy binary sensors."""

    def tests_binary_sensor_properties(self, m):
        """Tests that binary sensor device properties work as expected."""
        # Set up URL's
        m.post(CONST.LOGIN_URL, text=LOGIN.post_response_ok())
        m.get(CONST.OAUTH_TOKEN_URL, text=OAUTH_CLAIMS.get_response_ok())
        m.post(CONST.LOGOUT_URL, text=LOGOUT.post_response_ok())
        m.get(CONST.PANEL_URL, text=PANEL.get_response_ok(mode=CONST.MODE_STANDBY))

        # Set up all Binary Sensor Devices in "off states"
        all_devices = (
            '['
            + DOOR_CONTACT.device(
                devid=DOOR_CONTACT.DEVICE_ID,
                status=CONST.STATUS_CLOSED,
                low_battery=False,
                no_response=False,
            )
            + ','
            + GLASS.device(
                devid=GLASS.DEVICE_ID,
                status=CONST.STATUS_OFFLINE,
                low_battery=False,
                no_response=False,
            )
            + ','
            + KEYPAD.device(
                devid=KEYPAD.DEVICE_ID,
                status=CONST.STATUS_OFFLINE,
                low_battery=False,
                no_response=False,
            )
            + ','
            + REMOTE_CONTROLLER.device(
                devid=REMOTE_CONTROLLER.DEVICE_ID,
                status=CONST.STATUS_OFFLINE,
                low_battery=False,
                no_response=False,
            )
            + ','
            + SIREN.device(
                devid=SIREN.DEVICE_ID,
                status=CONST.STATUS_OFFLINE,
                low_battery=False,
                no_response=False,
            )
            + ','
            + STATUS_DISPLAY.device(
                devid=STATUS_DISPLAY.DEVICE_ID,
                status=CONST.STATUS_OFFLINE,
                low_battery=False,
                no_response=False,
            )
            + ','
            + WATER_SENSOR.device(
                devid=WATER_SENSOR.DEVICE_ID,
                status=CONST.STATUS_OFFLINE,
                low_battery=False,
                no_response=False,
            )
            + ']'
        )

        m.get(CONST.DEVICES_URL, text=all_devices)

        # Logout to reset everything
        self.abode.logout()

        # Test our devices
        for device in self.abode.get_devices():
            assert not device.is_on, device.type + " is_on failed"
            assert not device.battery_low, device.type + " battery_low failed"
            assert not device.no_response, device.type + " no_response failed"

        # Set up all Binary Sensor Devices in "off states"
        all_devices = (
            '['
            + DOOR_CONTACT.device(
                devid=DOOR_CONTACT.DEVICE_ID,
                status=CONST.STATUS_OPEN,
                low_battery=True,
                no_response=True,
            )
            + ','
            + GLASS.device(
                devid=GLASS.DEVICE_ID,
                status=CONST.STATUS_ONLINE,
                low_battery=True,
                no_response=True,
            )
            + ','
            + KEYPAD.device(
                devid=KEYPAD.DEVICE_ID,
                status=CONST.STATUS_ONLINE,
                low_battery=True,
                no_response=True,
            )
            + ','
            + REMOTE_CONTROLLER.device(
                devid=REMOTE_CONTROLLER.DEVICE_ID,
                status=CONST.STATUS_ONLINE,
                low_battery=True,
                no_response=True,
            )
            + ','
            + SIREN.device(
                devid=SIREN.DEVICE_ID,
                status=CONST.STATUS_ONLINE,
                low_battery=True,
                no_response=True,
            )
            + ','
            + STATUS_DISPLAY.device(
                devid=STATUS_DISPLAY.DEVICE_ID,
                status=CONST.STATUS_ONLINE,
                low_battery=True,
                no_response=True,
            )
            + ','
            + WATER_SENSOR.device(
                devid=WATER_SENSOR.DEVICE_ID,
                status=CONST.STATUS_ONLINE,
                low_battery=True,
                no_response=True,
            )
            + ']'
        )

        m.get(CONST.DEVICES_URL, text=all_devices)

        # Refesh devices and test changes
        for device in skip_alarms(self.abode.get_devices(refresh=True)):
            assert device.is_on, device.type + " is_on failed"
            assert device.battery_low, device.type + " battery_low failed"
            assert device.no_response, device.type + " no_response failed"


def is_alarm(device):
    return device.type_tag == CONST.DEVICE_ALARM


skip_alarms = functools.partial(itertools.filterfalse, is_alarm)
