from pathlib import Path
from app.p29 import FORBIDDEN_ACTIONS,classify_output,validate_ai_request
ROOT=Path(__file__).parents[1];MAIN=(ROOT/'app/main.py').read_text();MIG=(ROOT/'alembic/versions/0029_ai_copilot.py').read_text()
def test_ai_is_assistive_and_always_draft():
    for purpose in ('DRAFT','SUMMARISE','PREPARE','SUGGEST'):assert validate_ai_request(purpose,'Prepare neutral text')==purpose
    assert classify_output('x')=={'classification':'AI_DRAFT','content':'x','requires_human_review':True,'autonomous_action':False}
    assert "classification='AI_DRAFT'" in MIG
def test_forbidden_ai_actions_fail_closed():
    for action in FORBIDDEN_ACTIONS:
        try:validate_ai_request('DRAFT',action);assert False
        except ValueError:pass
    assert 'AI_REQUEST_OUT_OF_SCOPE' in MAIN and 'AI_RUNTIME_NOT_CONFIGURED' in MAIN
def test_ai_requests_and_outputs_are_audited_per_tenant():
    for table in ('external_ai_draft_requests','external_ai_draft_outputs','external_ai_audit_events'):assert table in MIG
    assert 'tenant_id' in MIG and 'autonomous_actions":False' in MAIN
