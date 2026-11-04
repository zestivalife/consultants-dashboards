# Service configuration and migration matrix

| Service | Database version table | Required readiness dependencies | Current regression control | Gap |
|---|---|---|---|---|
| Auth | `alembic_version` | PostgreSQL, signing/session configuration | Auth migration and authority integration tests | required-setting inventory not centralized |
| Profile | `profile_service_alembic_version` | PostgreSQL | service migration-isolation test | readiness contract needs explicit config matrix test |
| Practice Operations | `practice_operations_alembic_version` | PostgreSQL, Fiteatsy delegated API for connected workflows | full regression plus database-backed lifecycle tests | downstream timeout matrix incomplete |
| Assessment | `assessment_service_alembic_version` | PostgreSQL, Redis | `test_database_engine_config.py` covers pool settings | startup required-variable matrix incomplete |
| Nutrition | `nutrition_service_alembic_version` | PostgreSQL, Redis | `test_database_engine_config.py` covers pool timeout | legacy/active ownership needs continued enforcement |
| Scoring | `scoring_engine_service_alembic_version` | PostgreSQL, Redis, Profile and Assessment APIs | `test_database_engine_config.py` covers pool timeout | service-to-service timeout contracts incomplete |
| Gateway | none | Auth and routed upstream services | Gateway regression suite | route registry drift gate not yet generated |
| Fiteatsy backend | SQL migration ledger | PostgreSQL, Redis for delegated replay/idempotency paths | migration governance and API/database suites | runtime SHA and Docker build-context controls missing |

## Permanent `db_pool_timeout` regression

Assessment, Nutrition and Scoring each construct SQLAlchemy engines with `settings.db_pool_timeout`. Every corresponding Settings model must declare a bounded integer value. The three service-local tests are consolidated on the reliability branch and execute before deployment through exact-SHA CI.

## Migration isolation rule

- A service may read and write only its owned Alembic version table.
- A migration runner must not infer another service's revision as its own.
- Migration collision, multiple unexpected heads or foreign revision values must fail before application startup.
- Production stamping or history correction is never automatic.
- Upgrade and rollback feasibility must be tested in an isolated production-compatible database.

## Release classification

The following are independently required:

1. build success;
2. migration success;
3. process startup;
4. health success;
5. dependency readiness success;
6. authentication and RBAC enforcement;
7. functional provider/consumer contract success;
8. exact source and image provenance.

Railway `SUCCESS` satisfies only the platform deployment state and cannot replace these gates.
