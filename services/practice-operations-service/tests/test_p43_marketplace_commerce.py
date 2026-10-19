from pathlib import Path
import pytest
from app.p43 import assert_paid_evidence,split_amount
ROOT=Path(__file__).parents[1];MAIN=(ROOT/'app/main.py').read_text();MIGRATION=(ROOT/'alembic/versions/0043_marketplace_commerce.py').read_text()
def test_deterministic_minor_unit_split_and_rounding():
    assert split_amount(gross_minor=10001,tax_minor=1000,discount_minor=500,provider_fee_minor=101,commission_type='PERCENTAGE',commission_value='12.5')=={'gross_minor':10001,'tax_minor':1000,'discount_minor':500,'platform_fee_minor':1063,'consultant_amount_minor':7438,'provider_fee_minor':101,'net_payout_minor':7337}
    assert split_amount(gross_minor=1000,commission_type='FIXED',commission_value='125')['net_payout_minor']==875
def test_invalid_financial_values_fail_closed():
    with pytest.raises(ValueError):split_amount(gross_minor=100,discount_minor=101)
    with pytest.raises(ValueError):split_amount(gross_minor=100,commission_type='PERCENTAGE',commission_value='101')
def test_paid_requires_real_settlement_evidence():
    with pytest.raises(ValueError):assert_paid_evidence('PAID')
    assert assert_paid_evidence('PAID',manual_reference='bank-statement-1')
def test_append_only_external_schema_and_snapshot():
    assert '0042_calendar_sync' in MIGRATION
    for table in ('external_marketplace_commission_rules','external_marketplace_transactions','external_marketplace_payouts','external_marketplace_financial_ledger'):assert table in MIGRATION
    assert 'commission_snapshot JSONB NOT NULL' in MIGRATION and 'ON DELETE RESTRICT' in MIGRATION
    assert 'UPDATE external_marketplace_financial_ledger' not in MAIN
