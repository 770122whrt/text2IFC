"""Frozen native DSH search settings; credentials stay on the host gateway."""
from urllib.parse import urlsplit

SEARCH_VERSION = 'repair-comparison-dsh-search/0.1'
DEFAULT_SEARCH_BASE_URL = 'https://api.deepseek.com/anthropic/v1'


def validate_search_configuration(value):
    fields = {'schema_version', 'endpoint', 'model', 'max_tokens', 'max_uses'}
    if not isinstance(value, dict) or set(value) != fields or value['schema_version'] != SEARCH_VERSION:
        raise ValueError('INVALID_DSH_SEARCH_CONFIGURATION')
    endpoint = urlsplit(value['endpoint'])
    if (endpoint.scheme != 'https' or not endpoint.hostname or endpoint.username or endpoint.password
            or endpoint.query or endpoint.fragment or not endpoint.path.endswith('/messages')):
        raise ValueError('INVALID_DSH_SEARCH_ENDPOINT')
    if not isinstance(value['model'], str) or not value['model'].strip():
        raise ValueError('INVALID_DSH_SEARCH_MODEL')
    for field, maximum in (('max_tokens', 65536), ('max_uses', 5)):
        if type(value[field]) is not int or not 0 < value[field] <= maximum:
            raise ValueError('INVALID_DSH_SEARCH_LIMIT')
    return dict(value)


def search_configuration(environment, *, model='deepseek-v4-flash'):
    base = environment.get('DEEPSEEK_SEARCH_BASE_URL') or DEFAULT_SEARCH_BASE_URL
    return validate_search_configuration({'schema_version': SEARCH_VERSION,
        'endpoint': base.rstrip('/') + '/messages', 'model': model, 'max_tokens': 4096, 'max_uses': 5})


def search_api_key(environment, settings):
    validate_search_configuration(settings)
    key = environment.get('DEEPSEEK_SEARCH_API_KEY')
    if not key and urlsplit(settings['endpoint']).hostname == 'api.deepseek.com':
        key = environment.get('DEEPSEEK_API_KEY')
    if not key or not key.strip() or key.strip() in {'XXXX', 'YOUR_API_KEY'}:
        raise ValueError('SEARCH_CREDENTIAL_REQUIRED')
    return key


def validate_search_request(body, settings):
    """Only the official auxiliary server-search request may use this route."""
    if set(body) - {'model', 'max_tokens', 'messages', 'tools', 'stream'}:
        raise ValueError('SEARCH_REQUEST_FIELDS_NOT_OFFERED')
    if body.get('stream', False) is not False:
        raise ValueError('SEARCH_STREAM_NOT_OFFERED')
    tools = body.get('tools')
    if (not isinstance(tools, list) or len(tools) != 1 or not isinstance(tools[0], dict)
            or set(tools[0]) != {'type', 'name', 'max_uses'}
            or tools[0].get('type') != 'web_search_20250305' or tools[0].get('name') != 'web_search'
            or type(tools[0].get('max_uses')) is not int
            or not 0 < tools[0]['max_uses'] <= settings['max_uses']):
        raise ValueError('SEARCH_SERVER_TOOL_NOT_OFFERED')
