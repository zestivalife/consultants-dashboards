from pathlib import Path

from app.p38 import project_post_session, resolve_post_session_actions

ROOT=Path(__file__).resolve().parents[1]

def test_profession_rules_are_deterministic_and_not_universal():
    physio={item["key"]:item["requirement"] for item in resolve_post_session_actions("PHYSIOTHERAPIST")}
    psychologist={item["key"]:item["requirement"] for item in resolve_post_session_actions("PSYCHOLOGIST")}
    assert physio["HOMEWORK"]=="REQUIRED"
    assert physio["NEXT_APPOINTMENT"]=="REQUIRED"
    assert psychologist["HOMEWORK"]=="RECOMMENDED"
    assert psychologist["REPORT"]=="NOT_APPLICABLE"

def test_operational_close_uses_required_actions_only():
    actions=resolve_post_session_actions("PHYSIOTHERAPIST")
    required={item["key"]:"COMPLETE" for item in actions if item["requirement"]=="REQUIRED"}
    projected=project_post_session(actions,{**required,"RESOURCE":"PENDING"})
    assert projected["sessionOperationallyClosed"] is True
    assert projected["completionPercent"]==100

def test_missing_required_action_blocks_operational_close():
    actions=resolve_post_session_actions("HEALTH_COACH")
    projected=project_post_session(actions,{"SESSION_NOTE":"COMPLETE","HOMEWORK":"COMPLETE","FOLLOWUP":"COMPLETE"})
    assert projected["sessionOperationallyClosed"] is False
    assert "GOAL" in projected["outstandingRequired"]

def test_package_and_milestone_add_reuse_actions_without_auto_execution():
    actions={item["key"]:item["requirement"] for item in resolve_post_session_actions("WELLNESS_CONSULTANT",package_low=True,milestone_due=True,report_due=True)}
    assert actions["RENEWAL"]=="RECOMMENDED"
    assert actions["GOAL"]=="REQUIRED"
    assert actions["REPORT"]=="REQUIRED"

def test_p38_api_guards_completed_sessions_and_never_auto_acts():
    source=(ROOT/"app/main.py").read_text()
    for value in ("COMPLETED_SESSION_REQUIRED","POST_SESSION_ACTIONS_PENDING","NO_FUTURE_SESSION","autoRenew","autoMessageSend","autonomousClinicalAction"):
        assert value in source
    assert 'session["status"]!="COMPLETED"' in source

def test_p38_migration_is_external_only_and_expand_only():
    source=(ROOT/"alembic/versions/0038_post_consultation_retention.py").read_text()
    assert "external_post_session_checklists" in source
    assert "external_post_session_events" in source
    assert "ALTER TABLE" not in source
    assert "expand-only" in source
