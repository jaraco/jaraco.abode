BASE = 'https://my.goabode.com/'

LOGIN = '/api/auth2/login'
LOGOUT = '/api/v1/logout'

OAUTH_TOKEN = '/api/auth2/claims'

PARAMS = '/api/v1/devices_beta/'

PANEL = '/api/v1/panel'

INTEGRATIONS = '/integrations/v1/devices/'
CAMERA_INTEGRATIONS = '/integrations/v1/camera/'


def panel_mode(area, mode):
    """Create panel URL."""
    return f'/api/v1/panel/mode/{area}/{mode}'


DEVICES = '/api/v1/devices'
DEVICE = '/api/v1/devices/{id}'

AREAS = '/api/v1/areas'

SETTINGS = '/api/v1/panel/setting'
SOUNDS = '/api/v1/sounds'
SIREN = '/api/v1/siren'

AUTOMATION = '/integrations/v1/automations/'
AUTOMATION_ID = AUTOMATION + '{id}/'
AUTOMATION_APPLY = AUTOMATION_ID + 'apply'

TIMELINE_IMAGES_ID = (
    '/api/v1/timeline?device_id={device_id}&dir=next&event_label=Image+Capture&size=1'
)
