"""Mock Abode Door Contact Device."""
import jaraco.abode.helpers.constants as CONST

from .. import dump


DEVICE_ID = 'RF:00000003'


def device(
    devid=DEVICE_ID,
    status=CONST.STATUS_CLOSED,
    low_battery=False,
    no_response=False,
    window=False,
):
    """Door contact mock device."""
    return dump(
        id=devid,
        type_tag='device_type.door_contact',
        type='Door Contact',
        name='Back Door',
        area='1',
        zone='2',
        sort_order=None,
        is_window=int(window),
        bypass='0',
        schar_24hr='0',
        sresp_mode_0='3',
        sresp_entry_0='3',
        sresp_exit_0='0',
        sresp_mode_1='1',
        sresp_entry_1='1',
        sresp_exit_1='0',
        sresp_mode_2='1',
        sresp_entry_2='1',
        sresp_exit_2='0',
        sresp_mode_3='1',
        sresp_entry_3='1',
        sresp_exit_3='0',
        version='',
        origin='abode',
        control_url='',
        deep_link=None,
        status_color='#5cb85c',
        faults={
            'low_battery': int(low_battery),
            'tempered': 0,
            'supervision': 0,
            'out_of_order': 0,
            'no_response': int(no_response),
        },
        status=status,
        statuses={'hvac_mode': None},
        status_ex='',
        actions=[],
        status_icons={
            'Open': 'assets/icons/door-open-red.svg',
            'Closed': 'assets/icons/door-closed-green.svg',
        },
        sresp_trigger='0',
        sresp_restore='0',
        icon='assets/icons/doorsensor-a.svg',
    )
