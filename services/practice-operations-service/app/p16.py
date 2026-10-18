from __future__ import annotations
import hashlib
from typing import Any

MAX_CHAIN_DEPTH = 3
OPERATORS = {"EQUALS","NOT_EQUALS","GREATER_THAN","GREATER_OR_EQUAL","LESS_THAN","LESS_OR_EQUAL","IN","NOT_IN","EXISTS","NOT_EXISTS"}
FIELD_REGISTRY = {
    "CLIENT.status", "APPOINTMENT.status", "PACKAGE.sessions_remaining", "INVOICE.balance_due",
    "HOMEWORK.status", "GOAL.status", "profession_code", "client_id",
}
SAFE_ACTIONS = {"CREATE_TASK","CREATE_FOLLOWUP","CREATE_PLAN_REVIEW","CREATE_RENEWAL_TASK","CREATE_INVOICE_REMINDER","CREATE_HOMEWORK_REVIEW","ADD_WAITLIST_ACTION","CREATE_APPOINTMENT_REMINDER"}
CONFIRMATION_ACTIONS = {"ASSIGN_ASSESSMENT","PREPARE_MESSAGE","CREATE_RESOURCE_ASSIGNMENT","CREATE_CLIENT_CHECKIN"}
ACTION_TYPES = SAFE_ACTIONS | CONFIRMATION_ACTIONS


def dotted_value(payload: dict[str, Any], field: str):
    value: Any = payload
    for part in field.split("."):
        if not isinstance(value, dict) or part not in value:
            return None
        value = value[part]
    return value


def evaluate_condition(payload: dict[str, Any], field: str, operator: str, expected: Any):
    if field not in FIELD_REGISTRY: raise ValueError("UNKNOWN_CONDITION_FIELD")
    if operator not in OPERATORS: raise ValueError("UNSUPPORTED_CONDITION_OPERATOR")
    actual = dotted_value(payload, field)
    if operator == "EXISTS": return actual is not None
    if operator == "NOT_EXISTS": return actual is None
    if operator == "EQUALS": return actual == expected
    if operator == "NOT_EQUALS": return actual != expected
    if operator == "IN": return actual in expected if isinstance(expected, list) else False
    if operator == "NOT_IN": return actual not in expected if isinstance(expected, list) else False
    if actual is None or expected is None: return False
    return {"GREATER_THAN":actual > expected,"GREATER_OR_EQUAL":actual >= expected,"LESS_THAN":actual < expected,"LESS_OR_EQUAL":actual <= expected}[operator]


def idempotency_key(tenant_id: str, version_id: str, event_id: str, action_index: int):
    raw=f"{tenant_id}:{version_id}:{event_id}:{action_index}".encode()
    return "automation:" + hashlib.sha256(raw).hexdigest()


def retry_state(attempt: int, max_retries: int, transient: bool):
    if not transient: return "FAILED"
    return "RETRYING" if attempt < max_retries else "DEAD_LETTERED"


def assert_chain_depth(depth: int):
    if depth >= MAX_CHAIN_DEPTH: raise ValueError("AUTOMATION_CHAIN_DEPTH_EXCEEDED")
