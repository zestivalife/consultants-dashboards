"""P26 location scope helpers."""
RESOURCE_TYPES=frozenset({'TEAM_MEMBER','CLIENT','APPOINTMENT','SERVICE','INVOICE','LEAD'})
def validate_resource_type(value):
    if value not in RESOURCE_TYPES:raise ValueError('Unsupported location resource type')
    return value
