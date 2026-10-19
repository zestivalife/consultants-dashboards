"""P43 deterministic marketplace commerce policy (integer minor units only)."""
from decimal import Decimal, ROUND_HALF_UP

COMMISSION_TYPES={"PERCENTAGE","FIXED","NONE"}

def split_amount(*,gross_minor:int,tax_minor:int=0,discount_minor:int=0,provider_fee_minor:int=0,commission_type:str="NONE",commission_value:str="0"):
    if commission_type not in COMMISSION_TYPES:raise ValueError("Unsupported commission type")
    if min(gross_minor,tax_minor,discount_minor,provider_fee_minor)<0:raise ValueError("Amounts cannot be negative")
    chargeable=gross_minor-tax_minor-discount_minor
    if chargeable<0:raise ValueError("Tax and discount exceed gross amount")
    if commission_type=="PERCENTAGE":
        rate=Decimal(commission_value)
        if rate<0 or rate>100:raise ValueError("Percentage must be between 0 and 100")
        platform=int((Decimal(chargeable)*rate/Decimal(100)).quantize(Decimal("1"),rounding=ROUND_HALF_UP))
    elif commission_type=="FIXED":platform=int(Decimal(commission_value))
    else:platform=0
    if platform<0 or platform>chargeable:raise ValueError("Commission exceeds chargeable amount")
    consultant=chargeable-platform
    net=max(0,consultant-provider_fee_minor)
    return {"gross_minor":gross_minor,"tax_minor":tax_minor,"discount_minor":discount_minor,"platform_fee_minor":platform,"consultant_amount_minor":consultant,"provider_fee_minor":provider_fee_minor,"net_payout_minor":net}

def assert_paid_evidence(state:str,provider_reference=None,manual_reference=None):
    if state=="PAID" and not (provider_reference or manual_reference):raise ValueError("Paid payout requires settlement evidence")
    return True
