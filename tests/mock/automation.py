"""Mock Abode Automation."""

from . import dump


def get_response_ok(name, enabled, aid):
    """Return automation json."""
    return dump(
        name=name,
        enabled=str(enabled),
        version=2,
        id=aid,
        subType='',
        actions=[
            dict(
                directive=dict(
                    trait='panel.trains.panelMode',
                    name='panel.directives.arm',
                    state=dict(panelMode='AWAY'),
                )
            )
        ],
        conditions={},
        triggers=dict(
            operator='OR',
            expressions=list(
                dict(
                    mobileDevices=['89381', '658'],
                    property=dict(
                        trait='mobile.traits.location',
                        name='location',
                        location='31675',
                        equalTo='LAST_OUT',
                    ),
                )
            ),
        ),
    )
