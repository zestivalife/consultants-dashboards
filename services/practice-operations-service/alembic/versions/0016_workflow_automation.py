"""Add External-only workflow automation state on the existing outbox."""
from alembic import op

revision = "0016_workflow_automation"
down_revision = "0015_resources_homework"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""CREATE TABLE external_automation_definitions (
      id UUID PRIMARY KEY, tenant_id VARCHAR(80) NOT NULL, name VARCHAR(240) NOT NULL,
      description TEXT, profession_code VARCHAR(80), capability_required VARCHAR(80),
      trigger_type VARCHAR(80) NOT NULL, enabled BOOLEAN NOT NULL DEFAULT FALSE,
      current_version INTEGER NOT NULL DEFAULT 1, archived_at TIMESTAMPTZ,
      created_by VARCHAR(120) NOT NULL, created_at TIMESTAMPTZ NOT NULL, updated_at TIMESTAMPTZ NOT NULL,
      CONSTRAINT uq_external_automation_name UNIQUE (tenant_id,name)
    )""")
    op.execute("CREATE INDEX ix_external_automation_trigger ON external_automation_definitions(tenant_id,trigger_type,enabled)")
    op.execute("""CREATE TABLE external_automation_versions (
      id UUID PRIMARY KEY, definition_id UUID NOT NULL REFERENCES external_automation_definitions(id) ON DELETE RESTRICT,
      tenant_id VARCHAR(80) NOT NULL, version INTEGER NOT NULL, trigger_type VARCHAR(80) NOT NULL,
      requires_confirmation BOOLEAN NOT NULL DEFAULT FALSE, max_retries INTEGER NOT NULL DEFAULT 3,
      cooldown_minutes INTEGER, active_from TIMESTAMPTZ, active_until TIMESTAMPTZ,
      status VARCHAR(20) NOT NULL, created_by VARCHAR(120) NOT NULL, created_at TIMESTAMPTZ NOT NULL,
      CONSTRAINT uq_external_automation_version UNIQUE (definition_id,version)
    )""")
    op.execute("""CREATE TABLE external_automation_conditions (
      id UUID PRIMARY KEY, automation_version_id UUID NOT NULL REFERENCES external_automation_versions(id) ON DELETE RESTRICT,
      tenant_id VARCHAR(80) NOT NULL, condition_index INTEGER NOT NULL, field_key VARCHAR(100) NOT NULL,
      operator VARCHAR(30) NOT NULL, expected_value JSONB, created_at TIMESTAMPTZ NOT NULL,
      CONSTRAINT uq_external_automation_condition UNIQUE (automation_version_id,condition_index)
    )""")
    op.execute("""CREATE TABLE external_automation_actions (
      id UUID PRIMARY KEY, automation_version_id UUID NOT NULL REFERENCES external_automation_versions(id) ON DELETE RESTRICT,
      tenant_id VARCHAR(80) NOT NULL, action_index INTEGER NOT NULL, action_type VARCHAR(80) NOT NULL,
      confirmation_required BOOLEAN NOT NULL DEFAULT FALSE, configuration JSONB NOT NULL DEFAULT '{}'::jsonb,
      created_at TIMESTAMPTZ NOT NULL,
      CONSTRAINT uq_external_automation_action UNIQUE (automation_version_id,action_index)
    )""")
    op.execute("""CREATE TABLE external_automation_executions (
      id UUID PRIMARY KEY, tenant_id VARCHAR(80) NOT NULL, automation_id UUID NOT NULL REFERENCES external_automation_definitions(id),
      automation_version_id UUID NOT NULL REFERENCES external_automation_versions(id), event_id UUID NOT NULL REFERENCES service_outbox_events(id),
      client_id VARCHAR(120), status VARCHAR(30) NOT NULL, attempt_count INTEGER NOT NULL DEFAULT 0,
      execution_depth INTEGER NOT NULL DEFAULT 0, condition_results JSONB NOT NULL DEFAULT '[]'::jsonb,
      error_code VARCHAR(80), error_summary VARCHAR(500), next_retry_at TIMESTAMPTZ,
      started_at TIMESTAMPTZ, completed_at TIMESTAMPTZ, created_at TIMESTAMPTZ NOT NULL,
      CONSTRAINT uq_external_automation_execution UNIQUE (tenant_id,automation_version_id,event_id)
    )""")
    op.execute("CREATE INDEX ix_external_automation_execution_history ON external_automation_executions(tenant_id,created_at DESC)")
    op.execute("""CREATE TABLE external_automation_action_results (
      id UUID PRIMARY KEY, tenant_id VARCHAR(80) NOT NULL, execution_id UUID NOT NULL REFERENCES external_automation_executions(id),
      action_id UUID NOT NULL REFERENCES external_automation_actions(id), action_index INTEGER NOT NULL,
      action_type VARCHAR(80) NOT NULL, status VARCHAR(30) NOT NULL, target_type VARCHAR(80), target_id VARCHAR(120),
      result_summary VARCHAR(500), error_code VARCHAR(80), attempt_count INTEGER NOT NULL DEFAULT 0,
      approved_by VARCHAR(120), approved_at TIMESTAMPTZ, dismissed_by VARCHAR(120), dismissed_at TIMESTAMPTZ,
      created_at TIMESTAMPTZ NOT NULL, updated_at TIMESTAMPTZ NOT NULL,
      CONSTRAINT uq_external_automation_action_result UNIQUE (execution_id,action_index)
    )""")
    op.execute("""CREATE TABLE external_automation_idempotency_keys (
      tenant_id VARCHAR(80) NOT NULL, idempotency_key VARCHAR(240) NOT NULL,
      automation_version_id UUID NOT NULL, event_id UUID NOT NULL, action_index INTEGER NOT NULL,
      action_result_id UUID, created_at TIMESTAMPTZ NOT NULL,
      PRIMARY KEY (tenant_id,idempotency_key)
    )""")
    op.execute("""CREATE TABLE external_automation_audit_events (
      id UUID PRIMARY KEY, tenant_id VARCHAR(80) NOT NULL, automation_id UUID,
      automation_version_id UUID, execution_id UUID, action_result_id UUID,
      event_type VARCHAR(60) NOT NULL, actor_id VARCHAR(120) NOT NULL, actor_type VARCHAR(30) NOT NULL,
      metadata JSONB NOT NULL DEFAULT '{}'::jsonb, created_at TIMESTAMPTZ NOT NULL
    )""")
    op.execute("CREATE INDEX ix_external_automation_audit ON external_automation_audit_events(tenant_id,created_at DESC)")


def downgrade():
    raise RuntimeError("Workflow automation is expand-only")
