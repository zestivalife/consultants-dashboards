"""P14 External-only billing, invoices, payments, and receipts."""
from alembic import op

revision = "0014_billing"
down_revision = "0013_scheduling"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""CREATE TABLE external_billing_settings (
      tenant_id VARCHAR(80) PRIMARY KEY, practice_name VARCHAR(240), billing_address TEXT,
      tax_registration_number VARCHAR(80), default_currency VARCHAR(3) NOT NULL DEFAULT 'INR',
      default_tax_type VARCHAR(20) NOT NULL DEFAULT 'NO_TAX', default_tax_rate_bps INTEGER NOT NULL DEFAULT 0,
      invoice_prefix VARCHAR(24) NOT NULL DEFAULT 'INV', invoice_starting_number BIGINT NOT NULL DEFAULT 1,
      invoice_footer TEXT, payment_instructions TEXT, receipt_prefix VARCHAR(24) NOT NULL DEFAULT 'RCT',
      updated_by VARCHAR(120) NOT NULL, updated_at TIMESTAMPTZ NOT NULL,
      CONSTRAINT ck_external_billing_currency CHECK (default_currency ~ '^[A-Z]{3}$'),
      CONSTRAINT ck_external_billing_tax_type CHECK (default_tax_type IN ('NO_TAX','CGST_SGST','IGST','CUSTOM_TAX')),
      CONSTRAINT ck_external_billing_tax_rate CHECK (default_tax_rate_bps BETWEEN 0 AND 10000)
    )""")
    op.execute("""CREATE TABLE external_billable_services (
      id UUID PRIMARY KEY, tenant_id VARCHAR(80) NOT NULL, name VARCHAR(240) NOT NULL,
      description TEXT, category VARCHAR(120), default_price_minor BIGINT NOT NULL,
      currency VARCHAR(3) NOT NULL, default_tax_type VARCHAR(20) NOT NULL DEFAULT 'NO_TAX',
      default_tax_rate_bps INTEGER NOT NULL DEFAULT 0, active BOOLEAN NOT NULL DEFAULT TRUE,
      created_by VARCHAR(120) NOT NULL, created_at TIMESTAMPTZ NOT NULL, updated_at TIMESTAMPTZ NOT NULL,
      CONSTRAINT ck_external_billable_price CHECK (default_price_minor >= 0),
      CONSTRAINT ck_external_billable_tax CHECK (default_tax_rate_bps BETWEEN 0 AND 10000)
    )""")
    op.execute("CREATE INDEX ix_external_billable_services_tenant ON external_billable_services(tenant_id,active,name)")
    op.execute("""CREATE TABLE external_invoice_sequences (
      tenant_id VARCHAR(80) PRIMARY KEY, prefix VARCHAR(24) NOT NULL, next_number BIGINT NOT NULL,
      updated_at TIMESTAMPTZ NOT NULL, CONSTRAINT ck_external_invoice_next CHECK (next_number > 0)
    )""")
    op.execute("""CREATE TABLE external_invoices (
      id UUID PRIMARY KEY, tenant_id VARCHAR(80) NOT NULL, client_id VARCHAR(120) NOT NULL,
      invoice_number VARCHAR(80), status VARCHAR(20) NOT NULL DEFAULT 'DRAFT', currency VARCHAR(3) NOT NULL,
      issue_date DATE, due_date DATE, client_package_id UUID, appointment_id UUID, notes TEXT, terms TEXT,
      subtotal_minor BIGINT NOT NULL, discount_type VARCHAR(20) NOT NULL DEFAULT 'NONE',
      discount_value INTEGER NOT NULL DEFAULT 0, discount_amount_minor BIGINT NOT NULL DEFAULT 0,
      tax_total_minor BIGINT NOT NULL DEFAULT 0, grand_total_minor BIGINT NOT NULL,
      amount_paid_minor BIGINT NOT NULL DEFAULT 0, balance_due_minor BIGINT NOT NULL,
      tax_snapshot JSONB NOT NULL DEFAULT '{}'::jsonb, created_by VARCHAR(120) NOT NULL,
      issued_by VARCHAR(120), cancelled_by VARCHAR(120), created_at TIMESTAMPTZ NOT NULL,
      updated_at TIMESTAMPTZ NOT NULL, issued_at TIMESTAMPTZ, paid_at TIMESTAMPTZ, cancelled_at TIMESTAMPTZ,
      CONSTRAINT uq_external_invoice_number UNIQUE (tenant_id,invoice_number),
      CONSTRAINT ck_external_invoice_status CHECK (status IN ('DRAFT','ISSUED','PART_PAID','PAID','OVERDUE','CANCELLED')),
      CONSTRAINT ck_external_invoice_discount CHECK (discount_type IN ('NONE','FIXED','PERCENTAGE')),
      CONSTRAINT ck_external_invoice_totals CHECK (subtotal_minor >= 0 AND discount_amount_minor >= 0 AND tax_total_minor >= 0 AND grand_total_minor >= 0 AND amount_paid_minor >= 0 AND balance_due_minor >= 0),
      CONSTRAINT fk_external_invoice_package FOREIGN KEY (client_package_id) REFERENCES external_client_packages(id),
      CONSTRAINT fk_external_invoice_appointment FOREIGN KEY (appointment_id) REFERENCES external_scheduled_appointments(id)
    )""")
    op.execute("CREATE INDEX ix_external_invoices_tenant_status ON external_invoices(tenant_id,status,due_date)")
    op.execute("CREATE INDEX ix_external_invoices_client ON external_invoices(tenant_id,client_id,created_at)")
    op.execute("""CREATE TABLE external_invoice_items (
      id UUID PRIMARY KEY, tenant_id VARCHAR(80) NOT NULL, invoice_id UUID NOT NULL,
      service_id UUID, description VARCHAR(500) NOT NULL, quantity INTEGER NOT NULL,
      unit_price_minor BIGINT NOT NULL, discount_type VARCHAR(20) NOT NULL DEFAULT 'NONE',
      discount_value INTEGER NOT NULL DEFAULT 0, discount_amount_minor BIGINT NOT NULL DEFAULT 0,
      tax_type VARCHAR(20) NOT NULL DEFAULT 'NO_TAX', tax_rate_bps INTEGER NOT NULL DEFAULT 0,
      line_subtotal_minor BIGINT NOT NULL, line_tax_minor BIGINT NOT NULL, line_total_minor BIGINT NOT NULL,
      display_order INTEGER NOT NULL, CONSTRAINT fk_external_invoice_item_invoice FOREIGN KEY (invoice_id) REFERENCES external_invoices(id) ON DELETE CASCADE,
      CONSTRAINT fk_external_invoice_item_service FOREIGN KEY (service_id) REFERENCES external_billable_services(id),
      CONSTRAINT ck_external_invoice_item_values CHECK (quantity > 0 AND unit_price_minor >= 0 AND tax_rate_bps BETWEEN 0 AND 10000)
    )""")
    op.execute("CREATE INDEX ix_external_invoice_items_invoice ON external_invoice_items(tenant_id,invoice_id,display_order)")
    op.execute("""CREATE TABLE external_payment_records (
      id UUID PRIMARY KEY, tenant_id VARCHAR(80) NOT NULL, client_id VARCHAR(120) NOT NULL,
      invoice_id UUID NOT NULL, amount_minor BIGINT NOT NULL, currency VARCHAR(3) NOT NULL,
      method VARCHAR(30) NOT NULL, provenance VARCHAR(30) NOT NULL DEFAULT 'MANUAL_RECORDED',
      reference_number VARCHAR(160), provider_name VARCHAR(120), provider_reference VARCHAR(160),
      payment_date DATE NOT NULL, notes TEXT, recorded_by VARCHAR(120) NOT NULL, created_at TIMESTAMPTZ NOT NULL,
      CONSTRAINT fk_external_payment_invoice FOREIGN KEY (invoice_id) REFERENCES external_invoices(id),
      CONSTRAINT ck_external_payment_amount CHECK (amount_minor > 0),
      CONSTRAINT ck_external_payment_method CHECK (method IN ('CASH','BANK_TRANSFER','UPI','CARD_EXTERNAL','PAYMENT_GATEWAY','CHEQUE','OTHER')),
      CONSTRAINT ck_external_payment_provenance CHECK (provenance IN ('MANUAL_RECORDED','PROVIDER_CONFIRMED'))
    )""")
    op.execute("CREATE INDEX ix_external_payments_tenant ON external_payment_records(tenant_id,payment_date,invoice_id)")
    op.execute("""CREATE TABLE external_receipts (
      id UUID PRIMARY KEY, tenant_id VARCHAR(80) NOT NULL, client_id VARCHAR(120) NOT NULL,
      payment_id UUID NOT NULL UNIQUE, invoice_id UUID NOT NULL, receipt_number VARCHAR(80) NOT NULL,
      amount_minor BIGINT NOT NULL, currency VARCHAR(3) NOT NULL, remaining_balance_minor BIGINT NOT NULL,
      created_at TIMESTAMPTZ NOT NULL, CONSTRAINT uq_external_receipt_number UNIQUE (tenant_id,receipt_number),
      CONSTRAINT fk_external_receipt_payment FOREIGN KEY (payment_id) REFERENCES external_payment_records(id),
      CONSTRAINT fk_external_receipt_invoice FOREIGN KEY (invoice_id) REFERENCES external_invoices(id)
    )""")
    op.execute("""CREATE TABLE external_invoice_audit_events (
      id UUID PRIMARY KEY, tenant_id VARCHAR(80) NOT NULL, invoice_id UUID, service_id UUID,
      payment_id UUID, receipt_id UUID, event_type VARCHAR(40) NOT NULL, actor_id VARCHAR(120) NOT NULL,
      actor_type VARCHAR(30) NOT NULL, details JSONB NOT NULL DEFAULT '{}'::jsonb, created_at TIMESTAMPTZ NOT NULL
    )""")
    op.execute("CREATE INDEX ix_external_billing_audit_tenant ON external_invoice_audit_events(tenant_id,created_at)")


def downgrade():
    op.execute("DROP TABLE external_invoice_audit_events")
    op.execute("DROP TABLE external_receipts")
    op.execute("DROP TABLE external_payment_records")
    op.execute("DROP TABLE external_invoice_items")
    op.execute("DROP TABLE external_invoices")
    op.execute("DROP TABLE external_invoice_sequences")
    op.execute("DROP TABLE external_billable_services")
    op.execute("DROP TABLE external_billing_settings")
