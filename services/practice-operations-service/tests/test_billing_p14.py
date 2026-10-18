from pathlib import Path
from datetime import date

import pytest
from pydantic import ValidationError

from app.billing import calculate_line
from app.contracts import InvoiceCreate, InvoiceLineInput, PaymentCreate

ROOT=Path(__file__).parents[1]


def test_p14_migration_is_additive_external_only():
    source=(ROOT/"alembic/versions/0014_billing.py").read_text()
    for table in ("external_billing_settings","external_billable_services","external_invoice_sequences",
                  "external_invoices","external_invoice_items","external_payment_records",
                  "external_receipts","external_invoice_audit_events"):
        assert f"CREATE TABLE {table}" in source
    assert "ALTER TABLE" not in source
    assert "ZESTIVA_INTERNAL" not in source


def test_integer_money_tax_discount_and_rounding_are_deterministic():
    gst=calculate_line(1,140000,"NONE",0,1800)
    assert gst.tax_minor==25200 and gst.total_minor==165200
    bigger=calculate_line(1,300000,"NONE",0,1800)
    assert bigger.tax_minor==54000 and bigger.total_minor==354000
    discounted=calculate_line(2,10001,"PERCENTAGE",1250,1800)
    assert discounted.subtotal_minor==20002
    assert discounted.discount_minor==2500
    assert discounted.tax_minor==3150
    with pytest.raises(ValueError): calculate_line(1,10000,"FIXED",10001,0)


def test_invoice_and_payment_contracts_reject_unsafe_values():
    line=InvoiceLineInput(description="Review",quantity=1,unit_price_minor=140000,tax_type="CGST_SGST",tax_rate_bps=1800)
    invoice=InvoiceCreate(client_id="client-a",currency="INR",items=[line])
    payment=PaymentCreate(amount_minor=50000,currency="INR",method="UPI",payment_date=date(2026,10,18))
    assert invoice.items[0].unit_price_minor==140000 and payment.provenance=="MANUAL_RECORDED"
    with pytest.raises(ValidationError): PaymentCreate(amount_minor=0,currency="INR",method="CASH",payment_date=date.today())
    with pytest.raises(ValidationError): InvoiceLineInput(description="Bad",quantity=1,unit_price_minor=-1)


def test_billing_routes_are_tenant_scoped_atomic_immutable_and_audited():
    source=(ROOT/"app/main.py").read_text()
    section=source[source.index('@app.get("/api/v1/practice-operations/billing/services")'):]
    assert "tenant_id=:tenant" in section
    assert "FOR UPDATE" in section
    assert "external_invoice_sequences.next_number+1" in section
    assert "AND status='DRAFT'" in section
    assert "OVERPAYMENT_NOT_ALLOWED" in section
    assert "external_invoice_audit_events" in section
    assert "PAYMENT_GATEWAY" in (ROOT/"app/contracts.py").read_text()


def test_portal_only_projects_issued_financial_truth():
    source=(ROOT/"app/main.py").read_text()
    section=source[source.index('@app.get("/api/v1/client-portal/{token}")'):]
    assert "i.status IN ('ISSUED','PART_PAID','PAID','OVERDUE')" in section
    assert "external_receipts" in section
    assert "notes" not in section[section.index("invoices ="):section.index("receipts =")]
    assert "PAY_NOW" not in source
