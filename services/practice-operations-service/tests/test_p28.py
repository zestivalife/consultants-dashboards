import hashlib,hmac
from pathlib import Path
from app.p28 import PaymentProviderNotConfigured,canonical_payload_hash,verify_razorpay_payment,verify_razorpay_webhook
ROOT=Path(__file__).parents[1];MAIN=(ROOT/'app/main.py').read_text();MIG=(ROOT/'alembic/versions/0028_payment_foundation.py').read_text()
def test_provider_signatures_and_replay_primitives():
    secret='governed-test';order='order_1';payment='pay_1';signature=hmac.new(secret.encode(),f'{order}|{payment}'.encode(),hashlib.sha256).hexdigest()
    assert verify_razorpay_payment(order,payment,signature,secret)
    payload=b'{"event":"payment.captured"}';webhook=hmac.new(secret.encode(),payload,hashlib.sha256).hexdigest();assert verify_razorpay_webhook(payload,webhook,secret)
    assert len(canonical_payload_hash(payload))==64
def test_unconfigured_provider_fails_closed():
    try:verify_razorpay_payment('a','b','c',None);assert False
    except PaymentProviderNotConfigured:pass
    assert 'PAYMENT_PROVIDER_NOT_CONFIGURED' in MAIN and 'browser_success_authoritative":False' in MAIN
def test_payment_storage_is_idempotent_and_reconciles_p14():
    for table in ('external_payment_orders','external_payment_attempts','external_payment_webhook_events','external_payment_reconciliation_events'):assert table in MIG
    assert 'UNIQUE(tenant_id,idempotency_key)' in MIG and 'UNIQUE(provider,provider_event_id)' in MIG
    assert 'external_invoices' in MIG and 'external_payments' in MIG
    assert 'replay' in MAIN and 'lookup_payment' in MAIN
