"""
Mock Internal Alarm Device.

The library creates an internal device that is a standard panel response that
includes a few required device fields. This is so that we can easily translate
the panel/alarm itself into a Home Assistant device.
"""
import json

import jaraco.abode.helpers.constants as CONST

from .. import panel as PANEL


def device(area='1', panel=PANEL.get_response_ok(mode=CONST.MODE_STANDBY)):
    """Alarm mock device."""
    panel_ob = json.loads(panel)
    return dict(
        panel_ob,
        name=CONST.ALARM_NAME,
        id=CONST.ALARM_DEVICE_ID + area,
        type=CONST.ALARM_TYPE,
        type_tag=CONST.DEVICE_ALARM,
        generic_type=CONST.TYPE_ALARM,
        uuid=panel_ob.get('mac').replace(':', '').lower(),
    )
