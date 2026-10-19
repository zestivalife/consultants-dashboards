"""P40 deterministic teleconsultation policy without fabricated provider state."""
from datetime import timedelta
from urllib.parse import urlparse

def validate_external_meeting_url(value):
    if value is None:return None
    parsed=urlparse(value)
    if parsed.scheme!='https' or not parsed.netloc or parsed.username or parsed.password:raise ValueError('A credential-free HTTPS meeting URL is required')
    return value

def join_allowed(*,starts_at,ends_at,now,before_minutes=15,after_minutes=30,status='SCHEDULED'):
    return status not in {'CANCELLED','NO_SHOW','COMPLETED'} and starts_at-timedelta(minutes=before_minutes)<=now<=ends_at+timedelta(minutes=after_minutes)

def provider_status(mode):
    return 'NOT_CONFIGURED' if mode=='PROVIDER_NOT_CONFIGURED' else 'CONFIGURED'
