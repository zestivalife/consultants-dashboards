from pathlib import Path
import pytest
from app.p16 import (CONFIRMATION_ACTIONS, MAX_CHAIN_DEPTH, assert_chain_depth,
                     evaluate_condition, idempotency_key, retry_state)


def test_governed_condition_registry_and_operators():
    payload={"CLIENT":{"status":"ACTIVE"},"INVOICE":{"balance_due":500},"profession_code":"PHYSIOTHERAPIST"}
    assert evaluate_condition(payload,"CLIENT.status","EQUALS","ACTIVE")
    assert evaluate_condition(payload,"INVOICE.balance_due","GREATER_THAN",0)
    assert evaluate_condition(payload,"profession_code","IN",["PHYSIOTHERAPIST"])
    assert not evaluate_condition(payload,"GOAL.status","EXISTS",None)
    with pytest.raises(ValueError,match="UNKNOWN_CONDITION_FIELD"):
        evaluate_condition(payload,"CLIENT.password_hash","EQUALS","x")


def test_idempotency_is_deterministic_and_action_specific():
    first=idempotency_key("tenant","version","event",0)
    assert first==idempotency_key("tenant","version","event",0)
    assert first!=idempotency_key("tenant","version","event",1)


def test_retry_and_loop_prevention_are_bounded():
    assert retry_state(1,3,True)=="RETRYING"
    assert retry_state(3,3,True)=="DEAD_LETTERED"
    assert retry_state(1,3,False)=="FAILED"
    assert_chain_depth(MAX_CHAIN_DEPTH-1)
    with pytest.raises(ValueError,match="AUTOMATION_CHAIN_DEPTH_EXCEEDED"):
        assert_chain_depth(MAX_CHAIN_DEPTH)


def test_confirmation_and_communication_are_fail_closed():
    assert {"ASSIGN_ASSESSMENT","PREPARE_MESSAGE","CREATE_RESOURCE_ASSIGNMENT","CREATE_CLIENT_CHECKIN"}<=CONFIRMATION_ACTIONS
    text=(Path(__file__).parents[1]/"app/main.py").read_text()
    assert "PENDING_CONFIRMATION" in text
    assert "AUTOMATIC_MESSAGE_SEND" not in text
    assert "AUTO_CHARGE" not in text


def test_migration_reuses_outbox_and_is_freeze_safe():
    text=(Path(__file__).parents[1]/"alembic/versions/0016_workflow_automation.py").read_text()
    for table in ("external_automation_definitions","external_automation_versions","external_automation_conditions","external_automation_actions","external_automation_executions","external_automation_action_results","external_automation_idempotency_keys","external_automation_audit_events"):
        assert f"CREATE TABLE {table}" in text
    assert "ALTER TABLE" not in text
    assert "CREATE TABLE service_outbox" not in text


def test_engine_consumes_existing_outbox_and_records_delivery():
    text=(Path(__file__).parents[1]/"app/main.py").read_text()
    assert "FROM service_outbox_events WHERE id=:id AND tenant_id=:tenant" in text
    assert "P16_AUTOMATION_ENGINE" in text
    assert "writes_performed\":0" in text
    assert "created_at>=:cutoff" in text
