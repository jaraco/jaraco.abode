"""Timeline event constants."""

import csv

from importlib_resources import files
from jaraco.functools import call_aside
from jaraco.collections import RangeMap


# Timeline event groups.

ALARM_GROUP = 'abode_alarm'
ALARM_END_GROUP = 'abode_alarm_end'
PANEL_FAULT_GROUP = 'abode_panel_fault'
PANEL_RESTORE_GROUP = 'abode_panel_restore'
DISARM_GROUP = 'abode_disarm'
ARM_GROUP = 'abode_arm'
ARM_FAULT_GROUP = 'abode_arm_fault'
TEST_GROUP = 'abode_test'
CAPTURE_GROUP = 'abode_capture'
DEVICE_GROUP = 'abode_device'
AUTOMATION_GROUP = 'abode_automation'
AUTOMATION_EDIT_GROUP = 'abode_automation_edited'

ALL_EVENT_GROUPS = [
    ALARM_GROUP,
    ALARM_END_GROUP,
    PANEL_FAULT_GROUP,
    PANEL_RESTORE_GROUP,
    DISARM_GROUP,
    ARM_GROUP,
    ARM_FAULT_GROUP,
    TEST_GROUP,
    CAPTURE_GROUP,
    DEVICE_GROUP,
    AUTOMATION_GROUP,
    AUTOMATION_EDIT_GROUP,
]


event_code_mapping = RangeMap(
    {
        1099: RangeMap.undefined_value,
        1199: ALARM_GROUP,
        1299: RangeMap.undefined_value,
        1399: PANEL_FAULT_GROUP,
        1499: DISARM_GROUP,
        1599: RangeMap.undefined_value,
        1699: TEST_GROUP,
        3099: RangeMap.undefined_value,
        3199: ALARM_END_GROUP,
        3299: RangeMap.undefined_value,
        3399: PANEL_RESTORE_GROUP,
        3799: ARM_GROUP,
        3999: RangeMap.undefined_value,
        4001: ALARM_END_GROUP,
        4003: ARM_FAULT_GROUP,
        4999: RangeMap.undefined_value,
        5099: CAPTURE_GROUP,
        5199: DEVICE_GROUP,
        5299: AUTOMATION_GROUP,
        5999: RangeMap.undefined_value,
        6100: ARM_FAULT_GROUP,
    }
)
"""
The best inferred code mapping based on observed events.
Adjust as needed.
"""


def map_event_code(event_code):
    """Map a specific event_code to an event group."""
    return event_code_mapping.get(int(event_code))


def _read_events():
    with files().joinpath('events.csv').open() as strm:
        yield from csv.DictReader(strm, quoting=csv.QUOTE_NONE, skipinitialspace=True)


@call_aside
def _load_events():
    all_events = list(_read_events())
    vars = {
        event['var_name']: dict(event_code=event['code'], event_type=event['text'])
        for event in _read_events()
    }
    assert len(all_events) == len(vars)
    globals().update(vars)
