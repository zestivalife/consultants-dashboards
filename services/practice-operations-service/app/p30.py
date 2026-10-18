"""P30 export policy. This is operational evidence, not a legal compliance certification."""
import hashlib,json
ALLOWED_EXPORT_SECTIONS=frozenset({'CONSENTS','PORTAL_ACTIVITY','BILLING','DOCUMENTS','REFERRALS','AUTOMATIONS','AI_DRAFTS','FORMS','GOALS','TASKS','APPOINTMENTS','PROGRESS'})
EXCLUDED_BY_DEFAULT=frozenset({'PRIVATE_NOTES','RAW_SESSION_NOTES','INTERNAL_INTELLIGENCE','TEAM_NOTES'})
def validate_export_sections(sections):
    requested=set(sections)
    if requested-ALLOWED_EXPORT_SECTIONS:raise ValueError('One or more export sections are not permitted')
    return sorted(requested)
def export_checksum(payload):return hashlib.sha256(json.dumps(payload,sort_keys=True,default=str,separators=(',',':')).encode()).hexdigest()
