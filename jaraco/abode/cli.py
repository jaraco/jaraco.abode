"""Command-line interface."""

import os
import json
import logging
import time
import argparse
import contextlib
import getpass

import keyring

from . import Abode
from .helpers import constants as CONST
from .helpers import timeline as TIMELINE
from .exceptions import AbodeException

_LOGGER = logging.getLogger('abodecl')


def setup_logging(log_level=logging.INFO):
    """Set up the logging."""
    logging.basicConfig(level=log_level)
    fmt = "%(asctime)s %(levelname)s (%(threadName)s) " "[%(name)s] %(message)s"
    colorfmt = f"%(log_color)s{fmt}%(reset)s"
    datefmt = '%Y-%m-%d %H:%M:%S'

    # Suppress overly verbose logs from libraries that aren't helpful
    logging.getLogger('requests').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('aiohttp.access').setLevel(logging.WARNING)

    try:
        from colorlog import ColoredFormatter

        logging.getLogger().handlers[0].setFormatter(
            ColoredFormatter(
                colorfmt,
                datefmt=datefmt,
                reset=True,
                log_colors={
                    'DEBUG': 'cyan',
                    'INFO': 'green',
                    'WARNING': 'yellow',
                    'ERROR': 'red',
                    'CRITICAL': 'red',
                },
            )
        )
    except ImportError:
        pass

    logger = logging.getLogger('')
    logger.setLevel(log_level)


def build_parser():
    """
    Get parsed arguments.

    >>> parser = build_parser()
    """
    parser = argparse.ArgumentParser("abode")

    parser.add_argument(
        '-u', '--username', help='Username', default=os.environ.get('ABODE_USERNAME')
    )

    parser.add_argument('-p', '--password', help='Password')

    parser.add_argument('--mfa', help='Multifactor authentication code')

    parser.add_argument(
        '--cache',
        metavar='pickle_file',
        help='Create/update/use a pickle cache for the username and password.',
        default=CONST.CACHE_PATH,
    )

    parser.add_argument(
        '--mode',
        help='Output current alarm mode',
        default=False,
        action="store_true",
    )

    parser.add_argument(
        '--arm',
        metavar='mode',
        help='Arm alarm to mode',
    )

    parser.add_argument(
        '--set',
        metavar='setting=value',
        help='Set setting to a value',
        action='append',
    )

    parser.add_argument(
        '--devices',
        help='Output all devices',
        default=False,
        action="store_true",
    )

    parser.add_argument(
        '--device',
        metavar='device_id',
        help='Output one device for device_id',
        action='append',
    )

    parser.add_argument(
        '--json',
        metavar='device_id',
        help='Output the json for device_id',
        action='append',
    )

    parser.add_argument(
        '--on',
        metavar='device_id',
        help='Switch on a given device_id',
        action='append',
    )

    parser.add_argument(
        '--off',
        metavar='device_id',
        help='Switch off a given device_id',
        action='append',
    )

    parser.add_argument(
        '--lock',
        metavar='device_id',
        help='Lock a given device_id',
        action='append',
    )

    parser.add_argument(
        '--unlock',
        metavar='device_id',
        help='Unlock a given device_id',
        action='append',
    )

    parser.add_argument(
        '--automations',
        help='Output all automations',
        default=False,
        action="store_true",
    )

    parser.add_argument(
        '--activate',
        metavar='automation_id',
        help='Activate (enable) an automation by automation_id',
        action='append',
    )

    parser.add_argument(
        '--deactivate',
        metavar='automation_id',
        help='Deactivate (disable) an automation by automation_id',
        action='append',
    )

    parser.add_argument(
        '--trigger',
        metavar='automation_id',
        help='Trigger (apply) a manual (quick) automation by automation_id',
        action='append',
    )

    parser.add_argument(
        '--capture',
        metavar='device_id',
        help='Trigger a new image capture for the given device_id',
        action='append',
    )

    parser.add_argument(
        '--image',
        metavar='device_id=location/image.jpg',
        help='Save an image from a camera (if available) to the given path',
        action='append',
    )

    parser.add_argument(
        '--listen',
        help='Block and listen for device_id',
        default=False,
        action="store_true",
    )

    parser.add_argument(
        '--debug',
        help='Enable debug logging',
        default=False,
        action="store_true",
    )

    parser.add_argument(
        '--quiet',
        help='Output only warnings and errors',
        default=False,
        action="store_true",
    )

    return parser


def _create_abode_instance(args):
    return Abode(
        username=args.username,
        password=args.password,
        get_devices=args.mfa is None,
        cache_path=args.cache,
    )


@contextlib.contextmanager
def _log_errors_and_logout(abode):
    try:
        yield abode
    except abode.AbodeException as exc:
        _LOGGER.error(exc)
    finally:
        abode.logout()


def _device_print(dev, append=''):
    _LOGGER.info("%s%s", dev.desc, append)


def _device_callback(dev):
    _device_print(dev, ", At: " + time.strftime("%Y-%m-%d %H:%M:%S"))


def _timeline_callback(tl_json):
    event_code = int(tl_json['event_code'])
    if 5100 <= event_code <= 5199:
        # Ignore device changes
        return

    _LOGGER.info(
        "%s - %s at %s %s",
        tl_json['event_name'],
        tl_json['event_type'],
        tl_json['date'],
        tl_json['time'],
    )


class Dispatcher:
    def __init__(self, abode, args):
        self.abode = abode
        self.args = args

    def dispatch(self):
        self.login()
        self.output_current_mode()
        self.change_system_mode()
        self.set_setting()
        self.switch_on()
        self.switch_off()
        self.lock()
        self.unlock()
        self.output_json()
        self.print_all_automations()
        self.enable_automation()
        self.disable_automation()
        self.trigger_automation()
        self.trigger_image_capture()
        self.save_camera_image()
        self.print_all_devices()
        self.print_specific_devices()
        self.start_device_change_listener()

    def login(self):
        if not self.args.mfa:
            return
        self.abode.login(mfa_code=self.args.mfa)
        # fetch devices from Abode
        self.abode.get_devices()

    def output_current_mode(self):
        if not self.args.mode:
            return
        _LOGGER.info("Current alarm mode: %s", self.abode.get_alarm().mode)

    def change_system_mode(self):
        if not self.args.arm:
            return
        if self.abode.get_alarm().set_mode(self.args.arm):
            _LOGGER.info("Alarm mode changed to: %s", self.args.arm)
        else:
            _LOGGER.warning("Failed to change alarm mode to: %s", self.args.arm)

    def set_setting(self):
        for setting in self.args.set or []:
            keyval = setting.split("=")
            if self.abode.set_setting(keyval[0], keyval[1]):
                _LOGGER.info("Setting %s changed to %s", keyval[0], keyval[1])

    def switch_on(self):
        for device_id in self.args.on or []:
            device = self.abode.get_device(device_id)

            if device:
                if device.switch_on():
                    _LOGGER.info("Switched on device with id: %s", device_id)
            else:
                _LOGGER.warning("Could not find device with id: %s", device_id)

    def switch_off(self):
        for device_id in self.args.off or []:
            device = self.abode.get_device(device_id)

            if device:
                if device.switch_off():
                    _LOGGER.info("Switched off device with id: %s", device_id)
            else:
                _LOGGER.warning("Could not find device with id: %s", device_id)

    def lock(self):
        for device_id in self.args.lock or []:
            device = self.abode.get_device(device_id)

            if device:
                if device.lock():
                    _LOGGER.info("Locked device with id: %s", device_id)
            else:
                _LOGGER.warning("Could not find device with id: %s", device_id)

    def unlock(self):
        for device_id in self.args.unlock or []:
            device = self.abode.get_device(device_id)

            if device:
                if device.unlock():
                    _LOGGER.info("Unlocked device with id: %s", device_id)
            else:
                _LOGGER.warning("Could not find device with id: %s", device_id)

    def output_json(self):
        for device_id in self.args.json or []:
            device = self.abode.get_device(device_id)

            if device:
                print(
                    json.dumps(
                        device._state,
                        sort_keys=True,
                        indent=4,
                        separators=(',', ': '),
                    )
                )
            else:
                _LOGGER.warning("Could not find device with id: %s", device_id)

    def print_all_automations(self):
        if not self.args.automations:
            return
        for automation in self.abode.get_automations():
            _device_print(automation)

    def enable_automation(self):
        for automation_id in self.args.activate or []:
            automation = self.abode.get_automation(automation_id)

            if automation:
                if automation.enable(True):
                    _LOGGER.info("Activated automation with id: %s", automation_id)
            else:
                _LOGGER.warning("Could not find automation with id: %s", automation_id)

    def disable_automation(self):
        for automation_id in self.args.deactivate or []:
            automation = self.abode.get_automation(automation_id)

            if automation:
                if automation.enable(False):
                    _LOGGER.info("Deactivated automation with id: %s", automation_id)
            else:
                _LOGGER.warning("Could not find automation with id: %s", automation_id)

    def trigger_automation(self):
        for automation_id in self.args.trigger or []:
            automation = self.abode.get_automation(automation_id)

            if automation:
                if automation.trigger():
                    _LOGGER.info("Triggered automation with id: %s", automation_id)
            else:
                _LOGGER.warning("Could not find automation with id: %s", automation_id)

    def trigger_image_capture(self):
        for device_id in self.args.capture or []:
            device = self.abode.get_device(device_id)

            if device:
                if device.capture():
                    _LOGGER.info("Image requested from device with id: %s", device_id)
                else:
                    _LOGGER.warning(
                        "Failed to request image from device with id: %s", device_id
                    )
            else:
                _LOGGER.warning("Could not find device with id: %s", device_id)

    def save_camera_image(self):
        for keyval in self.args.image or []:
            devloc = keyval.split("=")
            device = self.abode.get_device(devloc[0])

            if device:
                try:
                    if device.refresh_image() and device.image_to_file(devloc[1]):
                        _LOGGER.info(
                            "Saved image to %s for device id: %s", devloc[1], devloc[0]
                        )
                except AbodeException as exc:
                    _LOGGER.warning("Unable to save image: %s", exc)
            else:
                _LOGGER.warning("Could not find device with id: %s", devloc[0])

    def print_all_devices(self):
        if not self.args.devices:
            return
        for device in self.abode.get_devices():
            _device_print(device)

    def print_specific_devices(self):
        if not self.args.device:
            return
        for device_id in self.args.device:
            device = self.abode.get_device(device_id)

            if device:
                _device_print(device)

                # Register the specific devices if we decide to listen.
                self.abode.events.add_device_callback(device_id, _device_callback)
            else:
                _LOGGER.warning("Could not find device with id: %s", device_id)

    def start_device_change_listener(self):
        if not self.args.listen:
            return
        # If no devices were specified then listen to all devices.
        if self.args.device is None:
            _LOGGER.info("Adding all devices to listener...")

            for device in self.abode.get_devices():
                self.abode.events.add_device_callback(
                    device.device_id, _device_callback
                )

        self.abode.events.add_timeline_callback(TIMELINE.ALL, _timeline_callback)

        _LOGGER.info("Listening for device and timeline updates...")
        self.abode.events.start()
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.abode.events.stop()
            _LOGGER.info("Device update listening stopped.")


def _get_password(args):
    if not args.username:
        raise SystemExit("Username unknown. Pass a username or set ABODE_USERNAME.")
    args.password = args.password or _get_or_set_password(args.username)


def _get_or_set_password(username):
    password = keyring.get_password(CONST.BASE_URL, username)
    if not password:
        password = getpass.getpass(f"Password for {username}: ")
        keyring.set_password(CONST.BASE_URL, username, password)
    return password


def main():
    """Execute command line helper."""
    args = build_parser().parse_args()
    _get_password(args)

    setup_logging(log_level=logging.INFO + 10 * (args.quiet - args.debug))

    with _log_errors_and_logout(_create_abode_instance(args)) as abode:
        Dispatcher(abode, args).dispatch()


if __name__ == '__main__':
    main()
