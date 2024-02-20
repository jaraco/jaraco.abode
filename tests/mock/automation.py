"""Mock Abode Automation."""


def get_response_ok(name: str, enabled: bool, id: str):
    """Return automation json."""
    assert isinstance(enabled, bool)
    return dict(
        name=name,
        enabled=enabled,
        id=id,
        version=2,
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
