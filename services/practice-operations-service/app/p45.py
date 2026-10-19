"""P45 server-authoritative promotion evaluation."""
from decimal import Decimal,ROUND_HALF_UP
def discount_minor(kind,value,amount_minor,maximum_discount_minor=None):
 if amount_minor<0:raise ValueError('Amount cannot be negative')
 if kind=='PERCENTAGE_DISCOUNT':
  rate=Decimal(str(value))
  if rate<0 or rate>100:raise ValueError('Percentage must be between 0 and 100')
  discount=int((Decimal(amount_minor)*rate/100).quantize(Decimal('1'),rounding=ROUND_HALF_UP))
 elif kind in {'FIXED_DISCOUNT','CREDIT','REFERRAL_CODE'}:discount=int(Decimal(str(value)))
 else:raise ValueError('Unsupported promotion type')
 if maximum_discount_minor is not None:discount=min(discount,maximum_discount_minor)
 return min(max(discount,0),amount_minor)
def validate_rule(rule,*,now,tenant_id,user_id,service_id=None,consultant_id=None,total_uses=0,user_uses=0,stacked=False,amount_minor=0):
 if not rule['active'] or now<rule['valid_from'] or (rule.get('valid_until') and now>=rule['valid_until']):raise ValueError('Promotion is not active')
 if rule.get('tenant_id') and rule['tenant_id']!=tenant_id:raise ValueError('Promotion tenant mismatch')
 if rule.get('usage_limit') is not None and total_uses>=rule['usage_limit']:raise ValueError('Promotion usage limit reached')
 if rule.get('per_user_limit') is not None and user_uses>=rule['per_user_limit']:raise ValueError('Promotion user limit reached')
 if rule.get('service_id') and rule['service_id']!=service_id:raise ValueError('Promotion is not valid for this service')
 if rule.get('consultant_id') and rule['consultant_id']!=consultant_id:raise ValueError('Promotion is not valid for this consultant')
 if amount_minor<rule.get('minimum_amount_minor',0):raise ValueError('Minimum amount not met')
 if stacked and not rule.get('stackable',False):raise ValueError('Promotion stacking is not allowed')
 return True
