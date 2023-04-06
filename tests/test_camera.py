"""Test the Abode camera class."""
import base64
import os
import pathlib
import re

import pytest

from jaraco.collections import Projection

import jaraco.abode
from jaraco.abode.helpers import urls
import jaraco.abode.devices.status as STATUS
from . import mock as MOCK
from .mock.devices import ipcam as IPCAM
from .mock.devices import ir_camera as IRCAMERA
from .mock import login as LOGIN
from .mock import logout as LOGOUT
from .mock import oauth_claims as OAUTH_CLAIMS
from .mock import panel as PANEL


cam_types = {
    'device_type.ipcam': IPCAM,
    'device_type.ir_camera': IRCAMERA,
}


def all_devices():
    return [
        IRCAMERA.device(
            devid=IRCAMERA.DEVICE_ID,
            status=STATUS.ONLINE,
            low_battery=False,
            no_response=False,
        ),
        IPCAM.device(
            devid=IPCAM.DEVICE_ID,
            status=STATUS.ONLINE,
            low_battery=False,
            no_response=False,
        ),
    ]


@pytest.fixture(autouse=True)
def setup_URLs(m):
    # Set up mock URLs
    m.post(urls.LOGIN, json=LOGIN.post_response_ok())
    m.get(urls.OAUTH_TOKEN, json=OAUTH_CLAIMS.get_response_ok())
    m.post(urls.LOGOUT, json=LOGOUT.post_response_ok())
    m.get(urls.PANEL, json=PANEL.get_response_ok(mode='standby'))
    m.get(urls.DEVICES, json=all_devices())


class TestCamera:
    """Test the camera."""

    def camera_devices(self):
        return (
            device
            for device in self.client.get_devices()
            if device.type_tag != 'device_type.alarm'
        )

    def test_camera_properties(self, m):
        """Tests that camera properties work as expected."""
        for device in self.camera_devices():
            # Specify which device module to use based on type_tag
            cam_type = cam_types[device.type_tag]

            # Test our device
            assert device is not None
            assert device.status == STATUS.ONLINE
            assert not device.battery_low
            assert not device.no_response

            # Set up our direct device get url
            device_url = urls.DEVICE.format(id=device.id)

            # Change device properties
            m.get(
                device_url,
                json=cam_type.device(
                    devid=cam_type.DEVICE_ID,
                    status=STATUS.OFFLINE,
                    low_battery=True,
                    no_response=True,
                ),
            )

            # Refesh device and test changes
            device.refresh()

            assert device.status == STATUS.OFFLINE
            assert device.battery_low
            assert device.no_response

    def test_camera_capture(self, m):
        """Tests that camera devices capture new images."""
        for device in self.camera_devices():
            # Specify which device module to use based on type_tag
            cam_type = cam_types[device.type_tag]

            # Test that we have the camera devices
            assert device is not None
            assert device.status == STATUS.ONLINE

            # Determine URL based on device type
            if device.type_tag == 'device_type.ipcam':
                url = cam_type.CONTROL_URL_SNAPSHOT

            elif device.type_tag == 'device_type.ir_camera':
                url = cam_type.CONTROL_URL

            # Set up capture URL response
            m.put(url, json=MOCK.generic_response_ok())

            # Capture an image
            assert device.capture()

            # Change capture URL responses
            m.put(url, json=cam_type.get_capture_timeout(), status_code=600)

            # Capture an image with a failure
            assert not device.capture()

    def test_camera_capture_no_control_URLs(self, m):
        """Tests that camera devices capture new images."""
        for device in self.camera_devices():
            # Hide any control URLs from the device state
            device._state = Projection(re.compile('(?!control_url).*'), device._state)

            # Test that jaraco.abode.Exception is raised with no control URLs
            with pytest.raises(jaraco.abode.Exception) as exc:
                device.capture()
            assert exc.value.message == "Control URL does not exist in device JSON."

    def test_camera_image_update(self, m):
        """Tests that camera devices update correctly via timeline request."""
        for device in self.camera_devices():
            # Specify which device module to use based on type_tag
            cam_type = cam_types[device.type_tag]

            # Test that we have our device
            assert device is not None
            assert device.status == STATUS.ONLINE

            # Set up timeline response
            url = urls.TIMELINE_IMAGES_ID.format(device_id=device.id)

            m.get(url, json=[cam_type.timeline_event(device.id)])
            # Set up our file path response
            m.head(
                cam_type.FILE_PATH,
                status_code=302,
                headers={"Location": cam_type.LOCATION_HEADER},
            )

            # Refresh the image
            assert device.refresh_image()

            # Verify the image location
            assert device.image_url == cam_type.LOCATION_HEADER

            # Test that a bad file_path response header results in an exception
            m.head(cam_type.FILE_PATH, status_code=302)

            with pytest.raises(jaraco.abode.Exception):
                device.refresh_image()

            # Test that a bad file_path response code results in an exception
            m.head(
                cam_type.FILE_PATH,
                status_code=200,
                headers={"Location": cam_type.LOCATION_HEADER},
            )

            with pytest.raises(jaraco.abode.Exception):
                device.refresh_image()

            # Test that an an empty timeline event throws exception
            url = urls.TIMELINE_IMAGES_ID.format(device_id=device.id)
            m.get(
                url,
                json=[cam_type.timeline_event(device.id, file_path="")],
            )

            with pytest.raises(jaraco.abode.Exception):
                device.refresh_image()

            # Test that an unexpected timeline event throws exception
            url = urls.TIMELINE_IMAGES_ID.format(device_id=device.id)
            m.get(
                url,
                json=[cam_type.timeline_event(device.id, event_code="1234")],
            )

            with pytest.raises(jaraco.abode.Exception):
                device.refresh_image()

    def test_camera_no_image_update(self, m):
        """Tests that camera updates correctly with no timeline events."""
        for device in self.camera_devices():
            # Test that we have our device
            assert device is not None
            assert device.status == STATUS.ONLINE

            # Set up timeline response
            url = urls.TIMELINE_IMAGES_ID.format(device_id=device.id)
            m.get(url, json=[])

            # Refresh the image
            assert not device.refresh_image()
            assert device.image_url is None

    def test_camera_image_write(self, m):
        """Tests that camera images will write to a file."""
        for device in self.camera_devices():
            # Specify which device module to use based on type_tag
            cam_type = cam_types[device.type_tag]

            # Test that we have our device
            assert device is not None
            assert device.status == STATUS.ONLINE

            # Set up timeline response
            url = urls.TIMELINE_IMAGES_ID.format(device_id=device.id)
            m.get(url, json=[cam_type.timeline_event(device.id)])

            # Set up our file path response
            m.head(
                cam_type.FILE_PATH,
                status_code=302,
                headers={"Location": cam_type.LOCATION_HEADER},
            )

            # Set up our image response
            image_response = "this is a beautiful jpeg image"
            m.get(cam_type.LOCATION_HEADER, json=image_response)

            # Refresh the image
            path = "test.jpg"
            assert device.image_to_file(path, get_image=True)

            # Test the file written and cleanup
            image_data = pathlib.Path(path).read_text(encoding='utf-8')
            assert image_response, image_data
            os.remove(path)

            # Test that bad response returns False
            m.get(cam_type.LOCATION_HEADER, status_code=400)
            with pytest.raises(jaraco.abode.Exception):
                device.image_to_file(path, get_image=True)

            # Test that the image fails to update returns False
            m.get(url, json=[])
            assert not device.image_to_file(path, get_image=True)

    def test_camera_snapshot(self, m):
        """Tests that camera devices capture new snapshots."""
        for device in self.camera_devices():
            # Specify which device module to use based on type_tag
            cam_type = cam_types[device.type_tag]

            # Test that we have our device
            assert device is not None
            assert device.status == STATUS.ONLINE

            # Set up snapshot URL response
            snapshot_url = f"{urls.CAMERA_INTEGRATIONS}{device.uuid}/snapshot"
            m.post(snapshot_url, json=dict(base64Image='test'))

            # Retrieve a snapshot
            assert device.snapshot()

            # Failed snapshot retrieval due to timeout response
            m.post(snapshot_url, json=cam_type.get_capture_timeout(), status_code=600)
            assert not device.snapshot()

            # Failed snapshot retrieval due to missing data
            m.post(snapshot_url, json={})
            assert not device.snapshot()

    def test_camera_snapshot_write(self, m):
        """Tests that camera snapshots will write to a file."""
        for device in self.camera_devices():
            # Specify which device module to use based on type_tag
            cam_type = cam_types[device.type_tag]

            # Test that we have our device
            assert device is not None
            assert device.status == STATUS.ONLINE

            # Set up snapshot URL and image response
            snapshot_url = f"{urls.CAMERA_INTEGRATIONS}{device.uuid}/snapshot"
            image_response = b"this is a beautiful jpeg image"
            b64_image = str(base64.b64encode(image_response), "utf-8")
            m.post(snapshot_url, json=dict(base64Image=b64_image))

            # Request the snapshot and write to file
            path = "test.jpg"
            assert device.snapshot_to_file(path, get_snapshot=True)

            # Test the file written and cleanup
            image_data = pathlib.Path(path).read_bytes()
            assert image_response == image_data
            os.remove(path)

            # Test that bad response returns False
            m.post(snapshot_url, json=cam_type.get_capture_timeout(), status_code=600)
            assert not device.snapshot_to_file(path, get_snapshot=True)

    def test_camera_snapshot_data_url(self, m):
        """Tests that camera snapshots can be converted to a data url."""
        for device in self.camera_devices():
            # Specify which device module to use based on type_tag
            cam_type = cam_types[device.type_tag]

            # Test that we have our device
            assert device is not None
            assert device.status == STATUS.ONLINE

            # Set up snapshot URL and image response
            snapshot_url = f"{urls.CAMERA_INTEGRATIONS}{device.uuid}/snapshot"
            image_response = b"this is a beautiful jpeg image"
            b64_image = str(base64.b64encode(image_response), "utf-8")
            m.post(snapshot_url, json=dict(base64Image=b64_image))

            # Request the snapshot as a data url
            data_url = device.snapshot_data_url(get_snapshot=True)

            # Test the data url matches the image response
            header, encoded = data_url.split(",", 1)
            decoded = base64.b64decode(encoded)
            assert header == "data:image/jpeg;base64"
            assert decoded == image_response

            # Test that bad response returns an empty string
            m.post(snapshot_url, json=cam_type.get_capture_timeout(), status_code=600)
            assert device.snapshot_data_url(get_snapshot=True) == ""

    def test_camera_privacy_mode(self, m):
        """Tests camera privacy mode."""

        # Get the IP camera and test we have it
        device = self.client.get_device(IPCAM.DEVICE_ID)
        assert device is not None
        assert device.status == STATUS.ONLINE

        # Set up params URL response for privacy mode on
        m.put(urls.PARAMS + device.id, json=IPCAM.device(privacy=1))

        # Set privacy mode on
        assert device.privacy_mode(True)

        # Set up params URL response for privacy mode off
        m.put(urls.PARAMS + device.id, json=IPCAM.device(privacy=0))

        # Set privacy mode off
        assert device.privacy_mode(False)

        # Test that an invalid privacy response throws exception
        with pytest.raises(jaraco.abode.Exception):
            device.privacy_mode(True)
