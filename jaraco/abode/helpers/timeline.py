"""Timeline event constants."""

import csv

from importlib_resources import files
from jaraco.functools import invoke
from jaraco.collections import RangeMap


class Groups:
    """Event groups."""

    ALARM = 'abode_alarm'
    ALARM_END = 'abode_alarm_end'
    PANEL_FAULT = 'abode_panel_fault'
    PANEL_RESTORE = 'abode_panel_restore'
    DISARM = 'abode_disarm'
    ARM = 'abode_arm'
    ARM_FAULT = 'abode_arm_fault'
    TEST = 'abode_test'
    CAPTURE = 'abode_capture'
    DEVICE = 'abode_device'
    AUTOMATION = 'abode_automation'
    AUTOMATION_EDIT = 'abode_automation_edited'
    ALL = list(locals().values())


event_code_mapping = RangeMap(
    {
        1099: RangeMap.undefined_value,
        1199: Groups.ALARM,
        1299: RangeMap.undefined_value,
        1399: Groups.PANEL_FAULT,
        1499: Groups.DISARM,
        1599: RangeMap.undefined_value,
        1699: Groups.TEST,
        3099: RangeMap.undefined_value,
        3199: Groups.ALARM_END,
        3299: RangeMap.undefined_value,
        3399: Groups.PANEL_RESTORE,
        3799: Groups.ARM,
        3999: RangeMap.undefined_value,
        4001: Groups.ALARM_END,
        4003: Groups.ARM_FAULT,
        4999: RangeMap.undefined_value,
        5099: Groups.CAPTURE,
        5199: Groups.DEVICE,
        5299: Groups.AUTOMATION,
        5999: RangeMap.undefined_value,
        6100: Groups.ARM_FAULT,
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
    with files().joinpath('events.csv').open(encoding='utf-8') as strm:
        yield from csv.DictReader(strm, quoting=csv.QUOTE_NONE, skipinitialspace=True)


@invoke
def _load_events():
    def var_name(event):
        default = (
            event['text']
            .replace(' - ', '_')
            .replace(' ', '_')
            .replace('/', '_')
            .upper()
        )
        return event['var_name'] or default

    all_events = list(_read_events())
    vars = {
        var_name(event): dict(event_code=event['code'], event_type=event['text'])
        for event in _read_events()
    }
    assert len(all_events) == len(vars)
    globals().update(vars)
