"""
Mock Internal Alarm Device.

The library creates an internal device that is a standard panel response that
includes a few required device fields. This is so that we can easily translate
the panel/alarm itself into a Home Assistant device.
"""

from jaraco.abode.devices import alarm

from .. import panel as PANEL


def device(area='1', panel=PANEL.get_response_ok(mode='standby')):
    """Alarm mock device."""
    return alarm.state_from_panel(panel)
