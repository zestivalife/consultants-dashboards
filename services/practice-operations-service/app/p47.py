"""P47 platform-support safety policy."""
TYPES={'TECHNICAL','ACCOUNT','BILLING','DATA','MARKETPLACE','INTEGRATION','FEATURE_REQUEST','OTHER'}
STATUSES={'OPEN','IN_PROGRESS','WAITING_ON_CUSTOMER','RESOLVED','CLOSED'}
SECRET_KEYS={'authorization','cookie','password','token','secret','api_key','refresh_token','access_token'}
def safe_context(value):
 if not isinstance(value,dict):raise ValueError('Support context must be an object')
 if any(any(secret in str(key).lower() for secret in SECRET_KEYS) for key in value):raise ValueError('Support context contains a secret-like key')
 allowed={'module','route','error_id','browser','build_sha'}
 return {key:str(item)[:500] for key,item in value.items() if key in allowed}
