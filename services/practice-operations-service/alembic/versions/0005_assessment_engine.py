"""External-only governed assessment engine."""
from alembic import op
from uuid import uuid5, NAMESPACE_URL

revision="0005_assessment_engine"
down_revision="0004_profession_p1"
branch_labels=None
depends_on=None

def upgrade():
    op.execute("""CREATE TABLE external_assessment_definitions (id UUID PRIMARY KEY, tenant_id VARCHAR(80), profession_code VARCHAR(80) NOT NULL, code VARCHAR(100) NOT NULL, title VARCHAR(200) NOT NULL, description TEXT, scope VARCHAR(20) NOT NULL, active BOOLEAN NOT NULL DEFAULT TRUE, created_by VARCHAR(120), created_at TIMESTAMPTZ NOT NULL, CONSTRAINT ck_external_assessment_scope CHECK (scope IN ('SYSTEM','PRACTICE')), CONSTRAINT uq_external_assessment_definition UNIQUE NULLS NOT DISTINCT (tenant_id,profession_code,code))""")
    op.execute("CREATE INDEX ix_external_assessment_definitions_scope ON external_assessment_definitions(profession_code,tenant_id,active)")
    op.execute("""CREATE TABLE external_assessment_versions (id UUID PRIMARY KEY, definition_id UUID NOT NULL REFERENCES external_assessment_definitions(id) ON DELETE RESTRICT, tenant_id VARCHAR(80), version INTEGER NOT NULL, status VARCHAR(20) NOT NULL, scoring_config JSONB NOT NULL DEFAULT '{}'::jsonb, published_at TIMESTAMPTZ, created_at TIMESTAMPTZ NOT NULL, CONSTRAINT ck_external_assessment_version_status CHECK (status IN ('DRAFT','ACTIVE','RETIRED')), CONSTRAINT uq_external_assessment_version UNIQUE(definition_id,version))""")
    op.execute("""CREATE TABLE external_assessment_questions (id UUID PRIMARY KEY, version_id UUID NOT NULL REFERENCES external_assessment_versions(id) ON DELETE CASCADE, tenant_id VARCHAR(80), question_key VARCHAR(100) NOT NULL, prompt TEXT NOT NULL, question_type VARCHAR(40) NOT NULL, required BOOLEAN NOT NULL DEFAULT FALSE, options JSONB NOT NULL DEFAULT '[]'::jsonb, sort_order INTEGER NOT NULL, CONSTRAINT uq_external_assessment_question UNIQUE(version_id,question_key))""")
    op.execute("""CREATE TABLE external_assessment_instances (id UUID PRIMARY KEY, tenant_id VARCHAR(80) NOT NULL, client_id VARCHAR(120) NOT NULL, definition_id UUID NOT NULL REFERENCES external_assessment_definitions(id) ON DELETE RESTRICT, version_id UUID NOT NULL REFERENCES external_assessment_versions(id) ON DELETE RESTRICT, profession_code VARCHAR(80) NOT NULL, status VARCHAR(24) NOT NULL DEFAULT 'ASSIGNED', assigned_by VARCHAR(120) NOT NULL, assigned_at TIMESTAMPTZ NOT NULL, due_at TIMESTAMPTZ, completed_at TIMESTAMPTZ, updated_at TIMESTAMPTZ NOT NULL, CONSTRAINT ck_external_assessment_instance_status CHECK (status IN ('ASSIGNED','IN_PROGRESS','COMPLETED','REVIEWED','CANCELLED')))""")
    op.execute("CREATE INDEX ix_external_assessment_instances_scope ON external_assessment_instances(tenant_id,client_id,status,assigned_at DESC)")
    op.execute("""CREATE TABLE external_assessment_answers (id UUID PRIMARY KEY, assessment_instance_id UUID NOT NULL REFERENCES external_assessment_instances(id) ON DELETE CASCADE, tenant_id VARCHAR(80) NOT NULL, client_id VARCHAR(120) NOT NULL, question_id UUID NOT NULL REFERENCES external_assessment_questions(id) ON DELETE RESTRICT, answer JSONB NOT NULL, answered_by VARCHAR(120) NOT NULL, answered_at TIMESTAMPTZ NOT NULL, CONSTRAINT uq_external_assessment_answer UNIQUE(assessment_instance_id,question_id))""")
    op.execute("CREATE INDEX ix_external_assessment_answers_scope ON external_assessment_answers(tenant_id,client_id,assessment_instance_id)")
    op.execute("""CREATE TABLE external_assessment_scores (id UUID PRIMARY KEY, assessment_instance_id UUID NOT NULL REFERENCES external_assessment_instances(id) ON DELETE RESTRICT, tenant_id VARCHAR(80) NOT NULL, client_id VARCHAR(120) NOT NULL, score_key VARCHAR(100) NOT NULL, numeric_value NUMERIC, label VARCHAR(120), explanation TEXT NOT NULL, calculated_at TIMESTAMPTZ NOT NULL, CONSTRAINT uq_external_assessment_score UNIQUE(assessment_instance_id,score_key))""")
    op.execute("""CREATE TABLE external_assessment_review_events (id UUID PRIMARY KEY, assessment_instance_id UUID NOT NULL REFERENCES external_assessment_instances(id) ON DELETE RESTRICT, tenant_id VARCHAR(80) NOT NULL, client_id VARCHAR(120) NOT NULL, event_type VARCHAR(40) NOT NULL, notes TEXT, actor_id VARCHAR(120) NOT NULL, created_at TIMESTAMPTZ NOT NULL)""")
    op.execute("CREATE INDEX ix_external_assessment_reviews_scope ON external_assessment_review_events(tenant_id,client_id,assessment_instance_id,created_at DESC)")
    templates={
      'DIABETES_EDUCATOR':['self-management','lifestyle-adherence','education-needs'],
      'PSYCHOLOGIST':['presenting-concern','mood-stress-self-report','therapy-goal-review'],
      'WELLNESS_CONSULTANT':['multidomain-wellness-review'],
      'HEALTH_COACH':['readiness-to-change','habit-baseline','weekly-check-in'],
      'BEHAVIOURAL_THERAPIST':['behaviour-baseline','behaviour-frequency-duration-intensity'],
      'OCCUPATIONAL_THERAPIST':['adl-function','participation','independence'],
      'PHYSIOTHERAPIST':['pain','functional-limitation','activity-impact'],
      'MENTAL_WELLNESS_THERAPIST':['stress-mood-sleep-coping','wellbeing-check-in'],
    }
    for profession,codes in templates.items():
        for code in codes:
            definition=uuid5(NAMESPACE_URL,f'zestiva:assessment:{profession}:{code}');version=uuid5(NAMESPACE_URL,f'{definition}:v1')
            title=code.replace('-',' ').title().replace('Adl','ADL')
            op.execute(f"INSERT INTO external_assessment_definitions(id,tenant_id,profession_code,code,title,description,scope,active,created_at) VALUES ('{definition}',NULL,'{profession}','{code}','{title}','Non-diagnostic practitioner-guided assessment.','SYSTEM',TRUE,now())")
            op.execute(f"INSERT INTO external_assessment_versions(id,definition_id,tenant_id,version,status,published_at,created_at) VALUES ('{version}','{definition}',NULL,1,'ACTIVE',now(),now())")
            questions=[('current_state','How would you describe the current situation?','TEXTAREA',True),('impact','How is this affecting daily life or progress?','TEXTAREA',True),('support_goal','What support or change would be most useful?','TEXTAREA',False)]
            for order,(key,prompt,qtype,required) in enumerate(questions,1):
                question=uuid5(NAMESPACE_URL,f'{version}:{key}')
                op.execute(f"INSERT INTO external_assessment_questions(id,version_id,tenant_id,question_key,prompt,question_type,required,sort_order) VALUES ('{question}','{version}',NULL,'{key}','{prompt}','{qtype}',{str(required).upper()},{order})")

def downgrade():
    for table in ('external_assessment_review_events','external_assessment_scores','external_assessment_answers','external_assessment_instances','external_assessment_questions','external_assessment_versions','external_assessment_definitions'):
        op.execute(f'DROP TABLE IF EXISTS {table}')
