"""Test the Abode device classes."""
import pytest

import jaraco.abode
from jaraco.abode.helpers import urls
from jaraco.abode.devices.base import Device
import jaraco.abode.devices.status as STATUS
from .mock import devices as DEVICES
from .mock.devices import door_contact as DOOR_CONTACT
from .mock.devices import glass as GLASS
from .mock.devices import power_switch_sensor as POWERSENSOR
from .mock.devices import unknown as UNKNOWN
from .mock import login as LOGIN
from .mock import oauth_claims as OAUTH_CLAIMS
from .mock import logout as LOGOUT
from .mock import panel as PANEL


class TestDevice:
    """Test the generic device class."""

    def test_device_mapping_type_tag(self):
        """Check new device without type_tag raises exception."""
        device = GLASS.device(
            status=STATUS.ONLINE,
            low_battery=True,
            no_response=True,
            tampered=True,
            out_of_order=True,
        )

        with pytest.raises(jaraco.abode.Exception):
            del device['type_tag']
            Device.new(device, self.client)

    def test_device_auto_naming(self):
        """Check the generic Abode device creates a name."""
        source = GLASS.device(
            status=STATUS.ONLINE,
            low_battery=True,
            no_response=True,
            tampered=True,
            out_of_order=True,
        )

        source['name'] = ""
        device = Device.new(source, self.client)
        generated_name = device.type + ' ' + device.id
        assert device.name == generated_name

        source['name'] = None
        device = Device.new(source, self.client)
        generated_name = device.type + ' ' + device.id
        assert device.name == generated_name

        del source['name']
        device = Device.new(source, self.client)
        generated_name = device.type + ' ' + device.id
        assert device.name == generated_name

    def test_device_init(self, m):
        """Check the generic Abode device class init's properly."""
        # Set up URLs
        m.post(urls.LOGIN, json=LOGIN.post_response_ok())
        m.get(urls.OAUTH_TOKEN, json=OAUTH_CLAIMS.get_response_ok())
        m.post(urls.LOGOUT, json=LOGOUT.post_response_ok())
        m.get(urls.PANEL, json=PANEL.get_response_ok())

        # Set up device
        source = [
            GLASS.device(
                status=STATUS.ONLINE,
                low_battery=True,
                no_response=True,
                tampered=True,
                out_of_order=True,
                uuid='testuuid00000001',
            )
        ]

        m.get(urls.DEVICES, json=source)

        # Logout to reset everything
        self.client.logout()

        # Get our specific device
        device = self.client.get_device(GLASS.DEVICE_ID)

        # Check device states match
        assert device is not None

        assert device.name == source[0]['name']
        assert device.type == source[0]['type']
        assert device.type_tag == source[0]['type_tag']
        assert device.id == source[0]['id']
        assert device.uuid == source[0]['uuid']
        assert device.status == STATUS.ONLINE
        assert device.battery_low
        assert device.no_response
        assert device.tampered
        assert device.out_of_order
        assert device.desc is not None

    def test_generic_device_refresh(self, m):
        """Check the generic Abode device class init's properly."""
        # Set up URLs
        m.post(urls.LOGIN, json=LOGIN.post_response_ok())
        m.get(urls.OAUTH_TOKEN, json=OAUTH_CLAIMS.get_response_ok())
        m.post(urls.LOGOUT, json=LOGOUT.post_response_ok())
        m.get(urls.PANEL, json=PANEL.get_response_ok())

        # Set up online device
        m.get(urls.DEVICES, json=[GLASS.device(status=STATUS.ONLINE)])

        # Set up offline device
        device_url = urls.DEVICE.format(id=GLASS.DEVICE_ID)
        m.get(device_url, json=[GLASS.device(status=STATUS.OFFLINE)])

        # Logout to reset everything
        self.client.logout()

        # Get the first device and test
        device = self.client.get_device(GLASS.DEVICE_ID)
        assert device.status == STATUS.ONLINE

        # Refresh the device and test
        device = self.client.get_device(GLASS.DEVICE_ID, refresh=True)
        assert device.status == STATUS.OFFLINE

    def test_multiple_devices(self, m):
        """Tests that multiple devices are returned properly."""
        # Set up URLs
        m.post(urls.LOGIN, json=LOGIN.post_response_ok())
        m.get(urls.OAUTH_TOKEN, json=OAUTH_CLAIMS.get_response_ok())
        m.post(urls.LOGOUT, json=LOGOUT.post_response_ok())
        m.get(urls.PANEL, json=PANEL.get_response_ok(mode='standby'))

        # Set up a list of devices
        dev_list = [
            POWERSENSOR.device(),
            DOOR_CONTACT.device(),
            GLASS.device(),
        ]

        m.get(urls.DEVICES, json=dev_list)

        # Logout to reset everything
        self.client.logout()

        # Get our devices
        devices = self.client.get_devices()

        # Assert four devices - three from above + 1 alarm
        assert devices is not None
        assert len(devices) == 4

        # Get each individual device by device ID
        psd = self.client.get_device(POWERSENSOR.DEVICE_ID)
        assert psd is not None

        # Get each individual device by device ID
        psd = self.client.get_device(DOOR_CONTACT.DEVICE_ID)
        assert psd is not None

        # Get each individual device by device ID
        psd = self.client.get_device(GLASS.DEVICE_ID)
        assert psd is not None

    def test_unknown_devices(self, m):
        """Tests that multiple devices are returned properly."""
        # Set up URLs
        m.post(urls.LOGIN, json=LOGIN.post_response_ok())
        m.get(urls.OAUTH_TOKEN, json=OAUTH_CLAIMS.get_response_ok())
        m.post(urls.LOGOUT, json=LOGOUT.post_response_ok())
        m.get(urls.PANEL, json=PANEL.get_response_ok(mode='standby'))

        m.get(urls.DEVICES, json=[UNKNOWN.device()])

        # Logout to reset everything
        self.client.logout()

        # Get our devices
        devices = self.client.get_devices()

        # Assert 1 device - skipped device above + 1 alarm
        assert devices is not None
        assert len(devices) == 1

    def test_device_category_filter(self, m):
        """Tests that device category filter returns requested results."""
        # Set up URLs
        m.post(urls.LOGIN, json=LOGIN.post_response_ok())
        m.get(urls.OAUTH_TOKEN, json=OAUTH_CLAIMS.get_response_ok())
        m.post(urls.LOGOUT, json=LOGOUT.post_response_ok())
        m.get(urls.PANEL, json=PANEL.get_response_ok(mode='standby'))

        # Set up a list of devices
        dev_list = [
            POWERSENSOR.device(
                devid='ps1',
                status=STATUS.OFF,
                low_battery=False,
                no_response=False,
            ),
            POWERSENSOR.device(
                devid='ps2',
                status=STATUS.OFF,
                low_battery=False,
                no_response=False,
            ),
            GLASS.device(
                devid='gb1',
                status=STATUS.OFF,
                low_battery=False,
                no_response=False,
            ),
        ]

        m.get(urls.DEVICES, json=dev_list)

        # Logout to reset everything
        self.client.logout()

        # Get our glass devices
        devices = self.client.get_devices(generic_type='connectivity')

        assert devices is not None
        assert len(devices) == 1

        # Get our power switch devices
        devices = self.client.get_devices(generic_type='switch')

        assert devices is not None
        assert len(devices) == 2

    def test_no_control_url(self, m):
        """Check that devices return false without control url's."""
        # Set up URLs
        m.post(urls.LOGIN, json=LOGIN.post_response_ok())
        m.get(urls.OAUTH_TOKEN, json=OAUTH_CLAIMS.get_response_ok())
        m.post(urls.LOGOUT, json=LOGOUT.post_response_ok())
        m.get(urls.PANEL, json=PANEL.get_response_ok())

        m.get(urls.DEVICES, json=GLASS.device(status=STATUS.ONLINE))

        # Logout to reset everything
        self.client.logout()

        # Get device
        device = self.client.get_device(GLASS.DEVICE_ID)

        assert device is not None
        with pytest.raises(jaraco.abode.Exception):
            device.set_status(1)
        with pytest.raises(jaraco.abode.Exception):
            device.set_level('99')

    def test_device_status_changes(self, m):
        """Tests that device status changes work as expected."""
        # Set up URLs
        m.post(urls.LOGIN, json=LOGIN.post_response_ok())
        m.get(urls.OAUTH_TOKEN, json=OAUTH_CLAIMS.get_response_ok())
        m.post(urls.LOGOUT, json=LOGOUT.post_response_ok())
        m.get(urls.PANEL, json=PANEL.get_response_ok(mode='standby'))
        m.get(
            urls.DEVICES,
            json=POWERSENSOR.device(
                devid=POWERSENSOR.DEVICE_ID,
                status=STATUS.OFF,
                low_battery=False,
                no_response=False,
            ),
        )

        # Logout to reset everything
        self.client.logout()

        # Get our power switch
        device = self.client.get_device(POWERSENSOR.DEVICE_ID)

        # Test that we have our device
        assert device is not None
        assert device.status == STATUS.OFF
        assert not device.is_on

        # Set up control url response
        control_url = POWERSENSOR.CONTROL_URL
        m.put(
            control_url,
            json=DEVICES.status_put_response_ok(
                devid=POWERSENSOR.DEVICE_ID, status=int(STATUS.ON)
            ),
        )

        # Change the mode to "on"
        device.switch_on()
        assert device.status == STATUS.ON
        assert device.is_on

        # Change response
        m.put(
            control_url,
            json=DEVICES.status_put_response_ok(
                devid=POWERSENSOR.DEVICE_ID, status=int(STATUS.OFF)
            ),
        )

        # Change the mode to "off"
        device.switch_off()
        assert device.status == STATUS.OFF
        assert not device.is_on

        # Test that an invalid device ID in response throws exception
        m.put(
            control_url,
            json=DEVICES.status_put_response_ok(
                devid='ZW:deadbeef', status=int(STATUS.OFF)
            ),
        )

        with pytest.raises(jaraco.abode.Exception):
            device.switch_on()

        # Test that an invalid status in response throws exception
        m.put(
            control_url,
            json=DEVICES.status_put_response_ok(
                devid=POWERSENSOR.DEVICE_ID, status=int(STATUS.OFF)
            ),
        )

        with pytest.raises(jaraco.abode.Exception):
            device.switch_on()

    def test_device_level_changes(self, m):
        """Tests that device level changes work as expected."""
        # Set up URLs
        m.post(urls.LOGIN, json=LOGIN.post_response_ok())
        m.get(urls.OAUTH_TOKEN, json=OAUTH_CLAIMS.get_response_ok())
        m.post(urls.LOGOUT, json=LOGOUT.post_response_ok())
        m.get(urls.PANEL, json=PANEL.get_response_ok(mode='standby'))

        # TODO: Test with a device that supports levels
        m.get(
            urls.DEVICES,
            json=POWERSENSOR.device(
                devid=POWERSENSOR.DEVICE_ID,
                status=STATUS.OFF,
                low_battery=False,
                no_response=False,
            ),
        )

        # Logout to reset everything
        self.client.logout()

        # Get our power switch
        device = self.client.get_device(POWERSENSOR.DEVICE_ID)

        # Test that we have our device
        assert device is not None
        assert device.status == STATUS.OFF
        assert not device.is_on

        # Set up control url response
        m.put(
            POWERSENSOR.CONTROL_URL,
            json=DEVICES.level_put_response_ok(
                devid=POWERSENSOR.DEVICE_ID, level='100'
            ),
        )

        # Change the level to int 100
        device.set_level(100)
        # self.assertEqual(device.level, '100')

        # Change response
        m.put(
            POWERSENSOR.CONTROL_URL,
            json=DEVICES.level_put_response_ok(devid=POWERSENSOR.DEVICE_ID, level='25'),
        )

        # Change the level to str '25'
        device.set_level('25')
        # self.assertEqual(device.level, '25')

        # Test that an invalid device ID in response throws exception
        m.put(
            POWERSENSOR.CONTROL_URL,
            json=DEVICES.level_put_response_ok(devid='ZW:deadbeef', level='25'),
        )

        with pytest.raises(jaraco.abode.Exception):
            device.set_level(25)

        # Test that an invalid level in response throws exception
        m.put(
            POWERSENSOR.CONTROL_URL,
            json=DEVICES.level_put_response_ok(devid=POWERSENSOR.DEVICE_ID, level='98'),
        )

        with pytest.raises(jaraco.abode.Exception):
            device.set_level('28')

    def test_all_devices(self, all_devices):
        """Tests that all mocked devices are mapped correctly."""

        # Logout to reset everything
        self.client.logout()

        # Loop through all devices
        for device in self.client.get_devices():
            class_type = Device.by_type().get(device.generic_type)

            assert class_type is not None, device.type + ' is not mapped.'
            assert isinstance(device, class_type)

    def test_get_devices_generic_type_substring(self, all_devices):
        """
        Test that a generic_type substring does not match in get_devices.
        """
        assert not self.client.get_devices(generic_type='nect')

    def test_get_devices_generic_type_superstring(self, all_devices):
        """
        Test that a generic_type superstring does not match in get_devices.
        """
        assert not self.client.get_devices(generic_type='connectivity-king')

    def test_get_devices_generic_type_simple_string(self, all_devices):
        """
        Test that a generic_type selects on a simple string.
        """
        selected = self.client.get_devices(generic_type='connectivity')
        all = self.client.get_devices()
        assert selected
        assert len(selected) < len(all)

    def test_get_devices_generic_type_list(self, all_devices):
        """
        Test that a generic_type can select a list of types.
        """
        types = 'door', 'connectivity'
        selected = self.client.get_devices(generic_type=types)
        assert selected
        door_devs = self.client.get_devices(generic_type='door')
        cnct_devs = self.client.get_devices(generic_type='connectivity')
        assert set(selected) == set(door_devs) | set(cnct_devs)
