from pathlib import Path
from app.p44 import downgrade_policy,entitled,provider_status
ROOT=Path(__file__).parents[1];M=(ROOT/'alembic/versions/0044_practice_subscriptions.py').read_text();MAIN=(ROOT/'app/main.py').read_text()
def test_entitlement_requires_all_independent_authorities():
 assert entitled(product_entitlement=True,role_permission=True,profession_capability=True)
 assert not entitled(product_entitlement=False,role_permission=True,profession_capability=True)
 assert not entitled(product_entitlement=True,role_permission=False,profession_capability=True)
def test_downgrade_preserves_data_and_provider_truth():
 assert downgrade_policy()=={'preserve_history':True,'restrict_new_usage':True,'delete_data':False}
 assert provider_status(False)=='NOT_CONFIGURED'
def test_linear_external_schema_is_separate_from_client_packages():
 assert '0043_marketplace_commerce' in M
 assert 'external_saas_plans' in M and 'external_practice_subscriptions' in M and 'external_subscription_events' in M
 assert 'external_client_packages' not in M and 'ALTER TABLE' not in M
 assert 'PRODUCT_AND_ROLE_AND_PROFESSION' in MAIN
