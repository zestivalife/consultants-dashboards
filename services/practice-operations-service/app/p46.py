"""P46 cancellation/refund truth and policy evaluation."""
REFUND_STATES={'REFUND_REQUESTED','REFUND_APPROVED','REFUND_PROCESSING','REFUNDED','REFUND_FAILED'}
def refund_transition(current,target,evidence=None):
 allowed={'REFUND_REQUESTED':{'REFUND_APPROVED','REFUND_FAILED'},'REFUND_APPROVED':{'REFUND_PROCESSING','REFUNDED','REFUND_FAILED'},'REFUND_PROCESSING':{'REFUNDED','REFUND_FAILED'},'REFUNDED':set(),'REFUND_FAILED':set()}
 if target not in allowed.get(current,set()):raise ValueError('Invalid refund transition')
 if target=='REFUNDED' and not evidence:raise ValueError('Refunded requires provider or manual evidence')
 return target
def refund_eligibility(policy,hours_before):
 if hours_before>=policy['full_refund_hours']:return {'kind':'FULL','percent':100}
 if hours_before>=policy['non_refundable_hours']:return {'kind':'PARTIAL','percent':policy['partial_refund_percent']}
 return {'kind':'NONE','percent':0}
