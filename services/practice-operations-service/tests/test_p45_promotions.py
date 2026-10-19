from datetime import datetime,timedelta,timezone
from pathlib import Path
import pytest
from app.p45 import discount_minor,validate_rule
ROOT=Path(__file__).parents[1];M=(ROOT/'alembic/versions/0045_promotions.py').read_text();MAIN=(ROOT/'app/main.py').read_text()
def rule(**extra):
 now=datetime.now(timezone.utc);base={'active':True,'valid_from':now-timedelta(days=1),'valid_until':now+timedelta(days=1),'tenant_id':'t1','usage_limit':10,'per_user_limit':1,'minimum_amount_minor':100,'stackable':False};base.update(extra);return base
def test_discount_is_bounded_and_never_negative():
 assert discount_minor('PERCENTAGE_DISCOUNT','12.5',1001)==125
 assert discount_minor('FIXED_DISCOUNT','2000',1000)==1000
 assert discount_minor('CREDIT','500',1000,300)==300
def test_rule_blocks_expiry_overuse_cross_tenant_and_stacking():
 now=datetime.now(timezone.utc)
 for changes,args in [({'valid_until':now-timedelta(seconds=1)},{}),({}, {'total_uses':10}),({}, {'user_uses':1}),({}, {'tenant_id':'t2'}),({}, {'stacked':True})]:
  with pytest.raises(ValueError):validate_rule(rule(**changes),now=now,tenant_id=args.get('tenant_id','t1'),user_id='u',total_uses=args.get('total_uses',0),user_uses=args.get('user_uses',0),stacked=args.get('stacked',False),amount_minor=1000)
def test_external_schema_and_server_authority():
 assert '0044_practice_subscriptions' in M and 'external_promotions' in M and 'external_promotion_redemptions' in M
 assert 'amount_after_minor=amount_before_minor-discount_minor' in M
 assert 'validate_rule(dict(rule)' in MAIN and 'PROMOTION_NOT_APPLICABLE' in MAIN
