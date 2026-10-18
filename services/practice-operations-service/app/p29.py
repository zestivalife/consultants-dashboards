"""Governed AI policy: assistive drafts only, never autonomous domain action."""
ALLOWED_PURPOSES=frozenset({'DRAFT','SUMMARISE','PREPARE','SUGGEST'})
FORBIDDEN_ACTIONS=frozenset({'DIAGNOSE','PRESCRIBE','PUBLISH_PLAN','PUBLISH_REPORT','SEND_MESSAGE','TAKE_PAYMENT','MUTATE_HEALTH_RECORD'})
def validate_ai_request(purpose,instruction):
    if purpose not in ALLOWED_PURPOSES:raise ValueError('Unsupported AI draft purpose')
    upper=instruction.upper().replace(' ','_')
    if any(action in upper for action in FORBIDDEN_ACTIONS):raise ValueError('Requested action is outside the assistive AI boundary')
    return purpose
def classify_output(content):return {'classification':'AI_DRAFT','content':content,'requires_human_review':True,'autonomous_action':False}
