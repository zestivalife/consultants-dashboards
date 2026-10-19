"""P48 notification projection over existing events; this is not a second event engine."""
CATEGORIES={'APPOINTMENT','CLIENT','TASK','ASSESSMENT','HOMEWORK','BILLING','MARKETPLACE','REVIEW','REFERRAL','REPORT','SUPPORT','SYSTEM'}
MANDATORY={'SECURITY','ACCOUNT_LOCKED','PAYMENT_FAILED','SYSTEM_OUTAGE'}
def category(event_type):
 value=str(event_type).upper()
 for name in CATEGORIES-{'SYSTEM'}:
  if name in value:return name
 return 'SYSTEM'
def effective_channels(preferences,event_type,providers):
 if event_type in MANDATORY:return {'in_app':True,'email':bool(providers.get('email')),'sms':False,'whatsapp':False}
 return {'in_app':bool(preferences.get('in_app',True)),'email':bool(preferences.get('email') and providers.get('email')),'sms':bool(preferences.get('sms') and providers.get('sms')),'whatsapp':bool(preferences.get('whatsapp') and providers.get('whatsapp'))}
def digest_mode(value):
 if value not in {'IMMEDIATE','DAILY','WEEKLY'}:raise ValueError('Unsupported notification digest mode')
 return value
