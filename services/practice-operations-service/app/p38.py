"""Deterministic P38 post-session operational policy."""

ACTION_ORDER=("SESSION_NOTE","HOMEWORK","RESOURCE","GOAL","FOLLOWUP","NEXT_APPOINTMENT","PLAN_REVIEW","REPORT","BILLING","RENEWAL")
BASE_RULES={"SESSION_NOTE":"REQUIRED","FOLLOWUP":"RECOMMENDED","NEXT_APPOINTMENT":"RECOMMENDED","HOMEWORK":"OPTIONAL","RESOURCE":"OPTIONAL","GOAL":"OPTIONAL","PLAN_REVIEW":"OPTIONAL","REPORT":"NOT_APPLICABLE","BILLING":"OPTIONAL","RENEWAL":"NOT_APPLICABLE"}
PROFESSION_RULES={
 "PSYCHOLOGIST":{"HOMEWORK":"RECOMMENDED","GOAL":"RECOMMENDED","FOLLOWUP":"REQUIRED"},
 "MENTAL_WELLNESS_THERAPIST":{"HOMEWORK":"RECOMMENDED","GOAL":"RECOMMENDED","FOLLOWUP":"REQUIRED"},
 "PHYSIOTHERAPIST":{"HOMEWORK":"REQUIRED","GOAL":"REQUIRED","NEXT_APPOINTMENT":"REQUIRED"},
 "HEALTH_COACH":{"HOMEWORK":"REQUIRED","GOAL":"REQUIRED","FOLLOWUP":"REQUIRED"},
 "DIABETES_EDUCATOR":{"HOMEWORK":"RECOMMENDED","RESOURCE":"RECOMMENDED","FOLLOWUP":"REQUIRED"},
 "OCCUPATIONAL_THERAPIST":{"HOMEWORK":"REQUIRED","GOAL":"REQUIRED"},
 "WELLNESS_CONSULTANT":{"HOMEWORK":"RECOMMENDED","RESOURCE":"RECOMMENDED","FOLLOWUP":"REQUIRED"},
 "BEHAVIOURAL_THERAPIST":{"HOMEWORK":"REQUIRED","GOAL":"RECOMMENDED","FOLLOWUP":"REQUIRED"},
}

def resolve_post_session_actions(profession_code,*,capabilities=(),package_low=False,milestone_due=False,report_due=False):
    rules=dict(BASE_RULES);rules.update(PROFESSION_RULES.get((profession_code or "").upper(),{}))
    capability_set={str(value).upper() for value in capabilities}
    if "PROGRESS_REPORTS" in capability_set or report_due:rules["REPORT"]="REQUIRED" if report_due else "RECOMMENDED"
    if "PROFESSION_PLANS" in capability_set:rules["PLAN_REVIEW"]="RECOMMENDED"
    if milestone_due:
        rules["GOAL"]="REQUIRED"
        if rules["REPORT"]=="NOT_APPLICABLE":rules["REPORT"]="RECOMMENDED"
    if package_low:rules["RENEWAL"]="RECOMMENDED"
    return [{"key":key,"requirement":rules[key]} for key in ACTION_ORDER]

def project_post_session(actions,evidence):
    items=[];required=[];complete=[]
    for configured in actions:
        key=configured["key"];requirement=configured["requirement"]
        status="NOT_REQUIRED" if requirement=="NOT_APPLICABLE" else evidence.get(key,"PENDING")
        items.append({**configured,"status":status})
        if requirement=="REQUIRED":
            required.append(key)
            if status=="COMPLETE":complete.append(key)
    closed=len(required)==len(complete)
    return {"items":items,"requiredCount":len(required),"requiredCompleteCount":len(complete),"completionPercent":100 if not required else int(len(complete)*100/len(required)),"sessionOperationallyClosed":closed,"outstandingRequired":[key for key in required if key not in complete]}
