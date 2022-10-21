"""Test the Abode camera class."""
import os

import pytest

import jaraco.abode
from jaraco.abode.exceptions import AbodeException
import jaraco.abode.helpers.constants as CONST
import jaraco.abode.helpers.errors as ERROR
import tests.mock as MOCK
import tests.mock.devices.ipcam as IPCAM
import tests.mock.devices.ir_camera as IRCAMERA
import tests.mock.login as LOGIN
import tests.mock.logout as LOGOUT
import tests.mock.oauth_claims as OAUTH_CLAIMS
import tests.mock.panel as PANEL


def set_cam_type(device_type):
    """Return camera type_tag."""
    if device_type == CONST.DEVICE_IP_CAM:
        return IPCAM

    if device_type == CONST.DEVICE_MOTION_CAMERA:
        return IRCAMERA


@pytest.fixture(autouse=True)
def all_devices(request):
    request.instance.all_devices = (
        "["
        + IRCAMERA.device(
            devid=IRCAMERA.DEVICE_ID,
            status=CONST.STATUS_ONLINE,
            low_battery=False,
            no_response=False,
        )
        + ","
        + IPCAM.device(
            devid=IPCAM.DEVICE_ID,
            status=CONST.STATUS_ONLINE,
            low_battery=False,
            no_response=False,
        )
        + "]"
    )


class TestCamera:
    """Test the AbodePy camera."""

    def tests_camera_properties(self, m):
        """Tests that camera properties work as expected."""
        # Set up URL's
        m.post(CONST.LOGIN_URL, text=LOGIN.post_response_ok())
        m.get(CONST.OAUTH_TOKEN_URL, text=OAUTH_CLAIMS.get_response_ok())
        m.post(CONST.LOGOUT_URL, text=LOGOUT.post_response_ok())
        m.get(CONST.PANEL_URL, text=PANEL.get_response_ok(mode=CONST.MODE_STANDBY))
        m.get(CONST.DEVICES_URL, text=self.all_devices)

        # Get our camera
        for device in self.abode.get_devices():
            # Skip alarm devices
            if device.type_tag == CONST.DEVICE_ALARM:
                continue

            # Specify which device module to use based on type_tag
            cam_type = set_cam_type(device.type_tag)

            # Test our device
            assert device is not None
            assert device.status == CONST.STATUS_ONLINE
            assert not device.battery_low
            assert not device.no_response

            # Set up our direct device get url
            device_url = CONST.DEVICE_URL.format(device_id=device.device_id)

            # Change device properties
            m.get(
                device_url,
                text=cam_type.device(
                    devid=cam_type.DEVICE_ID,
                    status=CONST.STATUS_OFFLINE,
                    low_battery=True,
                    no_response=True,
                ),
            )

            # Refesh device and test changes
            device.refresh()

            assert device.status == CONST.STATUS_OFFLINE
            assert device.battery_low
            assert device.no_response

    def tests_camera_capture(self, m):
        """Tests that camera devices capture new images."""
        # Set up URL's
        m.post(CONST.LOGIN_URL, text=LOGIN.post_response_ok())
        m.get(CONST.OAUTH_TOKEN_URL, text=OAUTH_CLAIMS.get_response_ok())
        m.post(CONST.LOGOUT_URL, text=LOGOUT.post_response_ok())
        m.get(CONST.PANEL_URL, text=PANEL.get_response_ok(mode=CONST.MODE_STANDBY))
        m.get(CONST.DEVICES_URL, text=self.all_devices)

        # Test our camera devices
        for device in self.abode.get_devices():
            # Skip alarm devices
            if device.type_tag == CONST.DEVICE_ALARM:
                continue

            # Specify which device module to use based on type_tag
            cam_type = set_cam_type(device.type_tag)

            # Test that we have the camera devices
            assert device is not None
            assert device.status == CONST.STATUS_ONLINE

            # Determine URL based on device type
            if device.type_tag == CONST.DEVICE_IP_CAM:
                url = CONST.BASE_URL + cam_type.CONTROL_URL_SNAPSHOT

            elif device.type_tag == CONST.DEVICE_MOTION_CAMERA:
                url = CONST.BASE_URL + cam_type.CONTROL_URL

            # Set up capture URL response
            m.put(url, text=MOCK.generic_response_ok())

            # Capture an image
            assert device.capture()

            # Change capture URL responses
            m.put(url, text=cam_type.get_capture_timeout(), status_code=600)

            # Capture an image with a failure
            assert not device.capture()

            # Remove control URLs from JSON to test if Abode makes
            # changes to JSON
            # pylint: disable=protected-access
            for key in list(device._json_state.keys()):
                if key.startswith("control_url"):
                    # pylint: disable=protected-access
                    del device._json_state[key]

            # Test that AbodeException is raised with no control URLs
            with pytest.raises(AbodeException) as exc:
                device.capture()
            assert (exc.value.errcode, exc.value.message) == ERROR.MISSING_CONTROL_URL

    def tests_camera_image_update(self, m):
        """Tests that camera devices update correctly via timeline request."""
        # Set up URL's
        m.post(CONST.LOGIN_URL, text=LOGIN.post_response_ok())
        m.get(CONST.OAUTH_TOKEN_URL, text=OAUTH_CLAIMS.get_response_ok())
        m.post(CONST.LOGOUT_URL, text=LOGOUT.post_response_ok())
        m.get(CONST.PANEL_URL, text=PANEL.get_response_ok(mode=CONST.MODE_STANDBY))
        m.get(CONST.DEVICES_URL, text=self.all_devices)

        # Test our camera devices
        for device in self.abode.get_devices():
            # Skip alarm devices
            if device.type_tag == CONST.DEVICE_ALARM:
                continue

            # Specify which device module to use based on type_tag
            cam_type = set_cam_type(device.type_tag)

            # Test that we have our device
            assert device is not None
            assert device.status == CONST.STATUS_ONLINE

            # Set up timeline response
            url = CONST.TIMELINE_IMAGES_ID_URL.format(device_id=device.device_id)

            m.get(url, text="[" + cam_type.timeline_event(device.device_id) + "]")
            # Set up our file path response
            file_path = CONST.BASE_URL + cam_type.FILE_PATH
            m.head(
                file_path,
                status_code=302,
                headers={"Location": cam_type.LOCATION_HEADER},
            )

            # Refresh the image
            assert device.refresh_image()

            # Verify the image location
            assert device.image_url == cam_type.LOCATION_HEADER

            # Test that a bad file_path response header results in an exception
            file_path = CONST.BASE_URL + cam_type.FILE_PATH
            m.head(file_path, status_code=302)

            with pytest.raises(jaraco.abode.AbodeException):
                device.refresh_image()

            # Test that a bad file_path response code results in an exception
            file_path = CONST.BASE_URL + cam_type.FILE_PATH
            m.head(
                file_path,
                status_code=200,
                headers={"Location": cam_type.LOCATION_HEADER},
            )

            with pytest.raises(jaraco.abode.AbodeException):
                device.refresh_image()

            # Test that an an empty timeline event throws exception
            url = CONST.TIMELINE_IMAGES_ID_URL.format(device_id=device.device_id)
            m.get(
                url,
                text="["
                + cam_type.timeline_event(device.device_id, file_path="")
                + "]",
            )

            with pytest.raises(jaraco.abode.AbodeException):
                device.refresh_image()

            # Test that an unexpected timeline event throws exception
            url = CONST.TIMELINE_IMAGES_ID_URL.format(device_id=device.device_id)
            m.get(
                url,
                text="["
                + cam_type.timeline_event(device.device_id, event_code="1234")
                + "]",
            )

            with pytest.raises(jaraco.abode.AbodeException):
                device.refresh_image()

    def tests_camera_no_image_update(self, m):
        """Tests that camera updates correctly with no timeline events."""
        # Set up URL's
        m.post(CONST.LOGIN_URL, text=LOGIN.post_response_ok())
        m.get(CONST.OAUTH_TOKEN_URL, text=OAUTH_CLAIMS.get_response_ok())
        m.post(CONST.LOGOUT_URL, text=LOGOUT.post_response_ok())
        m.get(CONST.PANEL_URL, text=PANEL.get_response_ok(mode=CONST.MODE_STANDBY))
        m.get(CONST.DEVICES_URL, text=self.all_devices)

        # Test our camera devices
        for device in self.abode.get_devices():
            # Skip alarm devices
            if device.type_tag == CONST.DEVICE_ALARM:
                continue

            # Test that we have our device
            assert device is not None
            assert device.status == CONST.STATUS_ONLINE

            # Set up timeline response
            url = CONST.TIMELINE_IMAGES_ID_URL.format(device_id=device.device_id)
            m.get(url, text="[]")

            # Refresh the image
            assert not device.refresh_image()
            assert device.image_url is None

    def tests_camera_image_write(self, m):
        """Tests that camera images will write to a file."""
        # Set up URL's
        m.post(CONST.LOGIN_URL, text=LOGIN.post_response_ok())
        m.get(CONST.OAUTH_TOKEN_URL, text=OAUTH_CLAIMS.get_response_ok())
        m.post(CONST.LOGOUT_URL, text=LOGOUT.post_response_ok())
        m.get(CONST.PANEL_URL, text=PANEL.get_response_ok(mode=CONST.MODE_STANDBY))
        m.get(CONST.DEVICES_URL, text=self.all_devices)

        # Test our camera devices
        for device in self.abode.get_devices():
            # Skip alarm devices
            if device.type_tag == CONST.DEVICE_ALARM:
                continue

            # Specify which device module to use based on type_tag
            cam_type = set_cam_type(device.type_tag)

            # Test that we have our device
            assert device is not None
            assert device.status == CONST.STATUS_ONLINE

            # Set up timeline response
            url = CONST.TIMELINE_IMAGES_ID_URL.format(device_id=device.device_id)
            m.get(url, text="[" + cam_type.timeline_event(device.device_id) + "]")

            # Set up our file path response
            file_path = CONST.BASE_URL + cam_type.FILE_PATH
            m.head(
                file_path,
                status_code=302,
                headers={"Location": cam_type.LOCATION_HEADER},
            )

            # Set up our image response
            image_response = "this is a beautiful jpeg image"
            m.get(cam_type.LOCATION_HEADER, text=image_response)

            # Refresh the image
            path = "test.jpg"
            assert device.image_to_file(path, get_image=True)

            # Test the file written and cleanup
            image_data = open(path, "r").read()
            assert image_response, image_data
            os.remove(path)

            # Test that bad response returns False
            m.get(cam_type.LOCATION_HEADER, status_code=400)
            with pytest.raises(jaraco.abode.AbodeException):
                device.image_to_file(path, get_image=True)

            # Test that the image fails to update returns False
            m.get(url, text="[]")
            assert not device.image_to_file(path, get_image=True)

    def tests_camera_privacy_mode(self, m):
        """Tests camera privacy mode."""
        # Set up mock URLs
        m.post(CONST.LOGIN_URL, text=LOGIN.post_response_ok())
        m.get(CONST.OAUTH_TOKEN_URL, text=OAUTH_CLAIMS.get_response_ok())
        m.post(CONST.LOGOUT_URL, text=LOGOUT.post_response_ok())
        m.get(CONST.PANEL_URL, text=PANEL.get_response_ok(mode=CONST.MODE_STANDBY))
        m.get(CONST.DEVICES_URL, text=self.all_devices)

        # Get the IP camera and test we have it
        device = self.abode.get_device(IPCAM.DEVICE_ID)
        assert device is not None
        assert device.status == CONST.STATUS_ONLINE

        # Set up params URL response for privacy mode on
        m.put(CONST.PARAMS_URL + device.device_id, text=IPCAM.device(privacy=1))

        # Set privacy mode on
        assert device.privacy_mode(True)

        # Set up params URL response for privacy mode off
        m.put(CONST.PARAMS_URL + device.device_id, text=IPCAM.device(privacy=0))

        # Set privacy mode off
        assert device.privacy_mode(False)

        # Test that an invalid privacy response throws exception
        with pytest.raises(jaraco.abode.AbodeException):
            device.privacy_mode(True)
