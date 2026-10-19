"""P44 commercial entitlement policy, separate from role and profession."""
STATES={"TRIAL","ACTIVE","PAST_DUE","CANCELLED","EXPIRED","SUSPENDED"}
def entitled(*,product_entitlement:bool,role_permission:bool,profession_capability:bool=True):return product_entitlement and role_permission and profession_capability
def provider_status(configured=False):return "CONFIGURED" if configured else "NOT_CONFIGURED"
def downgrade_policy():return {"preserve_history":True,"restrict_new_usage":True,"delete_data":False}
