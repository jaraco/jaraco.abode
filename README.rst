.. image:: https://img.shields.io/pypi/v/jaraco.abode.svg
   :target: `PyPI link`_

.. image:: https://img.shields.io/pypi/pyversions/jaraco.abode.svg
   :target: `PyPI link`_

.. _PyPI link: https://pypi.org/project/jaraco.abode

.. image:: https://github.com/jaraco/jaraco.abode/workflows/tests/badge.svg
   :target: https://github.com/jaraco/jaraco.abode/actions?query=workflow%3A%22tests%22
   :alt: tests

.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
   :target: https://github.com/psf/black
   :alt: Code style: Black

.. image:: https://readthedocs.org/projects/jaracoabode/badge/?version=latest
   :target: https://jaracoabode.readthedocs.io/en/latest/?badge=latest

.. image:: https://img.shields.io/badge/skeleton-2022-informational
   :target: https://blog.jaraco.com/skeleton

A thin Python library for the Abode alarm API.

Disclaimer:
~~~~~~~~~~~~~~~

"Abode" is a trademark owned by Abode Systems, Inc.; see www.goabode.com for
more information.

Thanks to Abode for having a relatively simple API to reverse engineer. Maybe in the future Abode will open it up for official use.

API calls faster than 60 seconds is not recommended as it can overwhelm Abode's servers. Leverage the cloud push event notification functionality as much as possible. Please use this module responsibly.
  
Command Line Usage
==================
Simple command line implementation arguments::

    $ abode --help
      usage: jaraco.abode: Command Line Utility [-h] -u USERNAME -p PASSWORD [--mode]
                                           [--arm mode] [--set setting=value]
                                           [--devices] [--device device_id]
                                           [--json device_id] [--on device_id]
                                           [--off device_id] [--lock device_id]
                                           [--unlock device_id] [--automations]
                                           [--activate automation_id]
                                           [--deactivate automation_id]
                                           [--trigger automation_id] [--listen]
                                           [--debug] [--quiet]
      
      optional arguments:
        -h, --help            show this help message and exit
        -u USERNAME, --username USERNAME
                              Username
        -p PASSWORD, --password PASSWORD
                              Password
        --mode                Output current alarm mode
        --arm mode            Arm alarm to mode
        --set setting=value   Set setting to a value
        --devices             Output all devices
        --device device_id    Output one device for device_id
        --json device_id      Output the json for device_id
        --on device_id        Switch on a given device_id
        --off device_id       Switch off a given device_id
        --lock device_id      Lock a given device_id
        --unlock device_id    Unlock a given device_id
        --automations         Output all automations
        --activate automation_id
                              Activate (enable) an automation by  automation_id
        --deactivate automation_id
                              Deactivate (disable) an automation by automation_id
        --trigger automation_id
                              Trigger (apply) an automation (manual quick-action) by
                              automation_id
        --listen              Block and listen for device_id
        --debug               Enable debug logging
        --quiet               Output only warnings and errors

You can get the current alarm mode::

    $ abode -u USERNAME -p PASSWORD --mode
    
      Mode: standby
    
To set the alarm mode, one of 'standby', 'home', or 'away'::

    $ abode -u USERNAME -p PASSWORD --arm home
    
      Mode set to: home

A full list of devices and their current states::

    $ abode -u USERNAME -p PASSWORD --devices
    
      Device Name: Glass Break Sensor, Device ID: RF:xxxxxxxx, Device Type: GLASS, Device Status: Online
      Device Name: Keypad, Device ID: RF:xxxxxxxx, Device Type: Keypad, Device Status: Online
      Device Name: Remote, Device ID: RF:xxxxxxxx, Device Type: Remote Controller, Device Status: Online
      Device Name: Garage Entry Door, Device ID: RF:xxxxxxxx, Device Type: Door Contact, Device Status: Closed
      Device Name: Front Door, Device ID: RF:xxxxxxxx, Device Type: Door Contact, Device Status: Closed
      Device Name: Back Door, Device ID: RF:xxxxxxxx, Device Type: Door Contact, Device Status: Closed
      Device Name: Status Indicator, Device ID: ZB:xxxxxxxx, Device Type: Status Display, Device Status: Online
      Device Name: Downstairs Motion Camera, Device ID: ZB:xxxxxxxx, Device Type: Motion Camera, Device Status: Online
      Device Name: Back Door Deadbolt, Device ID: ZW:xxxxxxxx, Device Type: Door Lock, Device Status: LockClosed
      Device Name: Front Door Deadbolt, Device ID: ZW:xxxxxxxx, Device Type: Door Lock, Device Status: LockClosed
      Device Name: Garage Door Deadbolt, Device ID: ZW:xxxxxxxx, Device Type: Door Lock, Device Status: LockClosed
      Device Name: Alarm area_1, Device ID: area_1, Device Type: Alarm, Device Status: standby

The current state of a specific device using the device id::

    $ abode -u USERNAME -p PASSWORD --device ZW:xxxxxxxx
    
      Device Name: Garage Door Deadbolt, Device ID: ZW:xxxxxxxx, Device Type: Door Lock, Device Status: LockClosed

Additionally, multiple specific devices using the device id::
    
    $ abode -u USERNAME -p PASSWORD --device ZW:xxxxxxxx --device RF:xxxxxxxx
    
      Device Name: Garage Door Deadbolt, Device ID: ZW:xxxxxxxx, Device Type: Door Lock, Device Status: LockClosed
      Device Name: Back Door, Device ID: RF:xxxxxxxx, Device Type: Door Contact, Device Status: Closed
    
You can switch a device on or off, or lock and unlock a device by passing multiple arguments::

    $ abode -u USERNAME -p PASSWORD --lock ZW:xxxxxxxx --switchOn ZW:xxxxxxxx
    
      Locked device with id: ZW:xxxxxxxx
      Switched on device with id: ZW:xxxxxxxx
   
You can also block and listen for all mode and change events as they occur::

    $ abode -u USERNAME -p PASSWORD --listen
    
      No devices specified, adding all devices to listener...
      Listening for device updates...
      Device Name: Alarm area_1, Device ID: area_1, Status: standby, At: 2017-05-27 11:13:08
      Device Name: Garage Door Deadbolt, Device ID: ZW:xxxxxxxx, Status: LockOpen, At: 2017-05-27 11:13:31
      Device Name: Garage Entry Door, Device ID: RF:xxxxxxxx, Status: Open, At: 2017-05-27 11:13:34
      Device Name: Garage Entry Door, Device ID: RF:xxxxxxxx, Status: Closed, At: 2017-05-27 11:13:39
      Device Name: Garage Door Deadbolt, Device ID: ZW:xxxxxxxx, Status: LockClosed, At: 2017-05-27 11:13:41
      Device Name: Alarm area_1, Device ID: area_1, Status: home, At: 2017-05-27 11:13:59
      Device update listening stopped.
        
If you specify one or more devices with the --device argument along with the --listen command then only those devices will listen for change events.

Keyboard interrupt (CTRL+C) to exit listening mode.

To obtain a list of automations::

    $ abode -u USERNAME -p PASSWORD --automations
    
      Deadbolts Lock Home (ID: 6) - status - active
      Auto Home (ID: 3) - location - active
      Lock Garage Quick Action (ID: 7) - manual - active
      Deadbolts Lock Away (ID: 5) - status - active
      Autostandby (ID: 4) - schedule - active
      Auto Away (ID: 2) - location - active
      Sleep Mode (ID: 1) - schedule - active
      
To activate or deactivate an automation::

    $ abode -u USERNAME -p PASSWORD --activate 1
    
      Activated automation with id: 1
      
To trigger a manual (quick) automation::

    $ abode -u USERNAME -p PASSWORD --trigger 7
    
      Triggered automation with id: 1

Settings
========

Change settings either using abode.set_setting(setting, value) or through the command line::

  $ abode -u USERNAME -p PASSWORD --set beeper_mute=1
  
    Setting beeper_mute changed to 1


.. list-table::
   :header-rows: 1

   * - Setting
     - Valid Values
   * - ircamera_resolution_t
     - 0 for 320x240x3, 2 for 640x480x3
   * - ircamera_gray_t
     - 0 for disabled, 1 for enabled
   * - beeper_mute
     - 0 for disabled, 1 for enabled
   * - away_entry_delay
     - 0, 10, 20, 30, 60, 120, 180, 240
   * - away_exit_delay
     - 30, 60, 120, 180, 240
   * - home_entry_delay
     - 0, 10, 20, 30, 60, 120, 180, 240
   * - home_exit_delay
     - 0, 10, 20, 30, 60, 120, 180, 240
   * - door_chime
     - none, normal, loud
   * - warning_beep
     - none, normal, loud
   * - entry_beep_away
     - none, normal, loud
   * - exit_beep_away
     - none, normal, loud
   * - entry_beep_home
     - none, normal, loud
   * - exit_beep_home
     - none, normal, loud
   * - confirm_snd
     - none, normal, loud
   * - alarm_len
     - 0, 60, 120, 180, 240, 300, 360, 420, 480, 540, 600, 660, 720, 780, 840, 900
   * - final_beep
     - 0, 3, 4, 5, 6, 7, 8, 9, 10
   * - entry
     - (Siren) 0 for disabled, 1 for enabled
   * - tamper
     - (Siren) 0 for disabled, 1 for enabled
   * - confirm
     - (Siren) 0 for disabled, 1 for enabled
