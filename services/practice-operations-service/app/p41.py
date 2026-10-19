"""P41 secure-message reference policy."""
MESSAGE_TYPES={'TEXT','RESOURCE_LINK','DOCUMENT_REFERENCE','APPOINTMENT_REFERENCE','FORM_LINK','CONSENT_LINK','REPORT_LINK'}
def validate_message(message_type,body=None,reference_id=None):
    if message_type not in MESSAGE_TYPES:raise ValueError('Unsupported message type')
    if message_type=='TEXT' and not (body and body.strip()):raise ValueError('Text is required')
    if message_type!='TEXT' and not reference_id:raise ValueError('A governed reference is required')
    if body and ('https://s3.' in body or 'X-Amz-Signature=' in body):raise ValueError('Raw private object URLs are not allowed')
    return True
