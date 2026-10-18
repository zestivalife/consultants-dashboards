"""Deterministic operational policy for the External Consultant command centre."""
from datetime import date, datetime, timezone

PRIORITY_ORDER={"URGENT_OPERATIONAL":0,"TODAY":1,"UPCOMING":2,"LOW":3}

ACTION_BY_SIGNAL={
    "TASK":("Open task","tasks"),
    "FOLLOW_UP":("Open follow-up","followups"),
    "HOMEWORK":("Review homework","resources"),
    "REPORT":("Open report","progress-reports"),
    "FOLLOWUP_OVERDUE":("Create follow-up","followups"),
    "TASK_OVERDUE":("Complete task","tasks"),
    "HOMEWORK_OVERDUE":("Review homework","client"),
    "ASSESSMENT_PENDING_REVIEW":("Review assessment","assessments"),
    "CONSENT_PENDING":("Request consent","consents"),
    "ONBOARDING_INCOMPLETE":("Review onboarding","client"),
    "INVOICE_OVERDUE":("Open invoice","billing"),
    "REPORT_PENDING":("Complete report","progress-reports"),
    "REFERRAL_PENDING":("Open referral","referrals"),
    "RENEWAL_DUE":("Prepare renewal","packages"),
    "PROGRAMME_ENDING":("Prepare renewal","packages"),
    "NO_FUTURE_APPOINTMENT":("Book appointment","calendar"),
}

def operational_priority(due_at=None, signal=""):
    """Classify urgency from due-time and operational state; never clinical risk."""
    now=datetime.now(timezone.utc)
    if due_at:
        if isinstance(due_at,date) and not isinstance(due_at,datetime):
            due_at=datetime.combine(due_at,datetime.min.time(),timezone.utc)
        elif due_at.tzinfo is None: due_at=due_at.replace(tzinfo=timezone.utc)
        hours=(due_at-now).total_seconds()/3600
        if hours<0:return "URGENT_OPERATIONAL"
        if hours<=24:return "TODAY"
        if hours<=168:return "UPCOMING"
    if signal in {"INVOICE_OVERDUE","FOLLOWUP_OVERDUE","TASK_OVERDUE","REPORT_PENDING"}:return "URGENT_OPERATIONAL"
    return "LOW"

def next_action(signal):
    label,target=ACTION_BY_SIGNAL.get(signal,("Open client","client"))
    return {"label":label,"target":target}

def section(items, *, failed=False, restricted=False, summary=None):
    if restricted:return {"status":"EMPTY_CONFIRMED","items":[],"restricted":True,"summary":summary or {}}
    if failed:return {"status":"FAILED","items":[],"summary":summary or {}}
    return {"status":"READY" if items else "EMPTY_CONFIRMED","items":items,"summary":summary or {}}

def sort_work(items):
    return sorted(items,key=lambda item:(PRIORITY_ORDER.get(item.get("priority"),9),str(item.get("due_at") or ""),str(item.get("id") or "")))
