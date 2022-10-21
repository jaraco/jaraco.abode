"""Mock Abode Glass Device."""
import jaraco.abode.helpers.constants as CONST

from .. import dump

DEVICE_ID = 'RF:00000001'


def device(
    devid=DEVICE_ID,
    status=CONST.STATUS_ONLINE,
    low_battery=False,
    no_response=False,
    out_of_order=False,
    tampered=False,
    uuid='91568b0d4c9d58c10d75fdeea887d4f4',
):
    """Glass break sensor mock device."""
    return dump(
        id=devid,
        type_tag='device_type.glass',
        type='GLASS',
        name='Glass Break Sensor',
        area='1',
        zone='6',
        sort_order=None,
        is_window='',
        bypass='0',
        schar_24hr='0',
        sresp_mode_0='0',
        sresp_entry_0='0',
        sresp_exit_0='0',
        sresp_mode_1='5',
        sresp_entry_1='5',
        sresp_exit_1='0',
        sresp_mode_2='5',
        sresp_entry_2='5',
        sresp_exit_2='0',
        sresp_mode_3='5',
        sresp_entry_3='5',
        sresp_exit_3='0',
        version='',
        origin='abode',
        control_url='',
        deep_link=None,
        status_color='#5cb85c',
        faults={
            'low_battery': int(low_battery),
            'tempered': int(tampered),
            'supervision': 0,
            'out_of_order': int(out_of_order),
            'no_response': int(no_response),
        },
        status=status,
        statuses={'hvac_mode': None},
        status_ex='',
        actions=[],
        status_icons=[],
        icon='assets/icons/unknown.svg',
        uuid=uuid,
    )
