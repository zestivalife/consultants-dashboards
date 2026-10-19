from pathlib import Path
import pytest
from app.p46 import refund_eligibility,refund_transition
ROOT=Path(__file__).parents[1];M=(ROOT/'alembic/versions/0046_refunds_credit_notes.py').read_text();MAIN=(ROOT/'app/main.py').read_text()
def test_configurable_policy_has_full_partial_and_none():
 p={'full_refund_hours':48,'non_refundable_hours':12,'partial_refund_percent':50}
 assert refund_eligibility(p,72)['kind']=='FULL';assert refund_eligibility(p,24)=={'kind':'PARTIAL','percent':50};assert refund_eligibility(p,2)['kind']=='NONE'
def test_refunded_requires_evidence_and_terminal_truth():
 with pytest.raises(ValueError):refund_transition('REFUND_APPROVED','REFUNDED')
 assert refund_transition('REFUND_PROCESSING','REFUNDED','provider-1')=='REFUNDED'
 with pytest.raises(ValueError):refund_transition('REFUNDED','REFUND_FAILED','x')
def test_non_destructive_external_schema_and_api():
 assert '0045_promotions' in M
 for table in ('external_cancellation_policies','external_refunds','external_credit_notes','external_refund_events'):assert table in M
 assert "state<>'REFUNDED' OR provider_refund_reference IS NOT NULL OR manual_refund_reference IS NOT NULL" in M
 assert 'REFERENCES external_payment_records(id)' in M
 assert 'REFERENCES external_payments(id)' not in M
 assert 'invoiceChanged":False' in MAIN and 'INSERT INTO external_credit_notes' in MAIN
 assert 'UPDATE external_invoices' not in MAIN[MAIN.index('@app.post("/api/v1/practice-operations/billing/refunds"'):]
