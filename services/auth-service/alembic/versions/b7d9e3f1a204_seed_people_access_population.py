"""seed people access population

Revision ID: b7d9e3f1a204
Revises: a8c4e2b7d901
Create Date: 2026-07-10 19:10:00
"""
from typing import Sequence, Union
import uuid
from datetime import date, datetime, timedelta, timezone

from alembic import op
import sqlalchemy as sa


revision: str = "b7d9e3f1a204"
down_revision: Union[str, None] = "a8c4e2b7d901"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


DEFAULT_PASSWORD_HASH = "$2b$12$wfj/jVj9BpKVYx/BYJZo5OiPlsprNVaQfZvUKBk6SypoBYZtMB5l2"
OWNER_EMAILS = [
    "zestivapriyanshi@gmail.com",
    "lalitppaunikar26@gmail.com",
]
ORGANIZATIONS = [
    ("Zenith Forge", "Manufacturing", "201-500"),
    ("Northstar Labs", "Diagnostics", "51-200"),
    ("Aster Pulse", "Healthcare", "51-200"),
    ("Atlas Commerce", "Retail", "201-500"),
    ("Meridian HealthOps", "HealthTech", "51-200"),
    ("Helio Foods", "Food & Beverage", "201-500"),
    ("Aquila Systems", "Technology", "501-1000"),
    ("BlueCrest Mobility", "Mobility", "201-500"),
    ("Cedar LifeCare", "Insurance", "201-500"),
    ("Orbit Wellness Works", "Corporate Wellness", "501-1000"),
]
DEPARTMENTS = ["Operations", "Clinical", "People Success", "Growth"]


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _slug(value: str) -> str:
    return value.lower().replace(" ", "-").replace("&", "and")


def upgrade() -> None:
    bind = op.get_bind()
    role_rows = bind.execute(sa.text("SELECT id, name FROM roles")).fetchall()
    product_rows = bind.execute(sa.text("SELECT id, key FROM products")).fetchall()
    package_rows = bind.execute(sa.text("SELECT id, product_id, code FROM package_catalog")).fetchall()
    service_rows = bind.execute(sa.text("SELECT id, product_id, code FROM service_catalog")).fetchall()

    role_ids = {row.name: row.id for row in role_rows}
    product_ids = {row.key: row.id for row in product_rows}
    package_ids = {}
    for row in package_rows:
        package_ids.setdefault(row.product_id, []).append(row.id)
    service_ids = {}
    for row in service_rows:
        service_ids.setdefault(row.product_id, []).append(row.id)

    users_table = sa.table(
        "users",
        sa.column("id", sa.Uuid()),
        sa.column("email", sa.String()),
        sa.column("password_hash", sa.String()),
        sa.column("company_name", sa.String()),
        sa.column("location", sa.String()),
        sa.column("employees", sa.Integer()),
        sa.column("industry", sa.String()),
        sa.column("role_id", sa.Uuid()),
        sa.column("is_active", sa.Boolean()),
        sa.column("is_verified", sa.Boolean()),
        sa.column("failed_login_attempts", sa.Integer()),
        sa.column("lock_until", sa.DateTime(timezone=True)),
        sa.column("first_name", sa.String()),
        sa.column("last_name", sa.String()),
        sa.column("phone", sa.String()),
        sa.column("avatar_url", sa.String()),
        sa.column("status", sa.String()),
        sa.column("permissions", sa.JSON()),
        sa.column("company_id", sa.Uuid()),
        sa.column("last_login_at", sa.DateTime(timezone=True)),
        sa.column("deleted_at", sa.DateTime(timezone=True)),
        sa.column("created_at", sa.DateTime(timezone=True)),
        sa.column("updated_at", sa.DateTime(timezone=True)),
    )
    organizations_table = sa.table(
        "organizations",
        sa.column("id", sa.Uuid()),
        sa.column("name", sa.String()),
        sa.column("logo_url", sa.Text()),
        sa.column("industry", sa.String()),
        sa.column("company_size", sa.String()),
        sa.column("gst_number", sa.String()),
        sa.column("address", sa.Text()),
        sa.column("timezone_name", sa.String()),
        sa.column("country", sa.String()),
        sa.column("subscription_name", sa.String()),
        sa.column("renewal_date", sa.Date()),
        sa.column("primary_contact_name", sa.String()),
        sa.column("primary_contact_email", sa.String()),
        sa.column("status", sa.String()),
        sa.column("created_by_user_id", sa.Uuid()),
        sa.column("created_at", sa.DateTime(timezone=True)),
        sa.column("updated_at", sa.DateTime(timezone=True)),
        sa.column("deactivated_at", sa.DateTime(timezone=True)),
    )
    departments_table = sa.table(
        "departments",
        sa.column("id", sa.Uuid()),
        sa.column("organization_id", sa.Uuid()),
        sa.column("name", sa.String()),
        sa.column("description", sa.Text()),
        sa.column("created_at", sa.DateTime(timezone=True)),
        sa.column("updated_at", sa.DateTime(timezone=True)),
    )
    organization_products_table = sa.table(
        "organization_products",
        sa.column("id", sa.Uuid()),
        sa.column("organization_id", sa.Uuid()),
        sa.column("product_id", sa.Uuid()),
        sa.column("status", sa.String()),
        sa.column("enabled_at", sa.DateTime(timezone=True)),
        sa.column("disabled_at", sa.DateTime(timezone=True)),
    )
    memberships_table = sa.table(
        "organization_memberships",
        sa.column("id", sa.Uuid()),
        sa.column("user_id", sa.Uuid()),
        sa.column("organization_id", sa.Uuid()),
        sa.column("department_id", sa.Uuid()),
        sa.column("employee_id", sa.String()),
        sa.column("package_name", sa.String()),
        sa.column("assigned_practitioner_id", sa.Uuid()),
        sa.column("assigned_mentor_id", sa.Uuid()),
        sa.column("assigned_consultant_id", sa.Uuid()),
        sa.column("primary_product_id", sa.Uuid()),
        sa.column("status", sa.String()),
        sa.column("is_verified", sa.Boolean()),
        sa.column("tags", sa.JSON()),
        sa.column("created_by_user_id", sa.Uuid()),
        sa.column("joined_at", sa.DateTime(timezone=True)),
        sa.column("created_at", sa.DateTime(timezone=True)),
        sa.column("updated_at", sa.DateTime(timezone=True)),
        sa.column("deactivated_at", sa.DateTime(timezone=True)),
    )
    user_roles_table = sa.table(
        "user_roles",
        sa.column("id", sa.Uuid()),
        sa.column("user_id", sa.Uuid()),
        sa.column("role_id", sa.Uuid()),
        sa.column("assigned_by_user_id", sa.Uuid()),
        sa.column("is_primary", sa.Boolean()),
        sa.column("created_at", sa.DateTime(timezone=True)),
    )
    user_product_access_table = sa.table(
        "user_product_access",
        sa.column("id", sa.Uuid()),
        sa.column("user_id", sa.Uuid()),
        sa.column("product_id", sa.Uuid()),
        sa.column("organization_id", sa.Uuid()),
        sa.column("role_id", sa.Uuid()),
        sa.column("status", sa.String()),
        sa.column("is_primary", sa.Boolean()),
        sa.column("permissions", sa.JSON()),
        sa.column("assigned_by_user_id", sa.Uuid()),
        sa.column("created_at", sa.DateTime(timezone=True)),
        sa.column("updated_at", sa.DateTime(timezone=True)),
    )
    user_package_assignments_table = sa.table(
        "user_package_assignments",
        sa.column("id", sa.Uuid()),
        sa.column("user_id", sa.Uuid()),
        sa.column("package_id", sa.Uuid()),
        sa.column("organization_id", sa.Uuid()),
        sa.column("product_id", sa.Uuid()),
        sa.column("status", sa.String()),
        sa.column("notes", sa.Text()),
        sa.column("assigned_by_user_id", sa.Uuid()),
        sa.column("started_at", sa.DateTime(timezone=True)),
        sa.column("ended_at", sa.DateTime(timezone=True)),
        sa.column("created_at", sa.DateTime(timezone=True)),
    )
    user_service_assignments_table = sa.table(
        "user_service_assignments",
        sa.column("id", sa.Uuid()),
        sa.column("user_id", sa.Uuid()),
        sa.column("service_id", sa.Uuid()),
        sa.column("organization_id", sa.Uuid()),
        sa.column("product_id", sa.Uuid()),
        sa.column("status", sa.String()),
        sa.column("notes", sa.Text()),
        sa.column("assigned_by_user_id", sa.Uuid()),
        sa.column("started_at", sa.DateTime(timezone=True)),
        sa.column("ended_at", sa.DateTime(timezone=True)),
        sa.column("created_at", sa.DateTime(timezone=True)),
    )

    owner_rows = bind.execute(
        sa.text("SELECT id, email FROM users WHERE email = ANY(:emails)")
        .bindparams(sa.bindparam("emails", expanding=True)),
        {"emails": OWNER_EMAILS},
    ).fetchall()
    owners_by_email = {row.email: row.id for row in owner_rows}
    owner_insert_rows = []
    for index, email in enumerate(OWNER_EMAILS):
        if email in owners_by_email:
            continue
        owner_id = uuid.UUID(f"66f4d9d8-6f1f-4d39-a101-5355d59500{index+1:02d}")
        owners_by_email[email] = owner_id
        owner_insert_rows.append(
            {
                "id": owner_id,
                "email": email,
                "password_hash": DEFAULT_PASSWORD_HASH,
                "company_name": "Nuetra Platform",
                "location": "India",
                "employees": None,
                "industry": "HealthTech",
                "role_id": role_ids["platform_owner"],
                "is_active": True,
                "is_verified": True,
                "failed_login_attempts": 0,
                "lock_until": None,
                "first_name": "Priyanshi" if "priyanshi" in email else "Lalit",
                "last_name": None if "priyanshi" in email else "Paunikar",
                "phone": None,
                "avatar_url": None,
                "status": "ACTIVE",
                "permissions": [],
                "company_id": None,
                "last_login_at": _now(),
                "deleted_at": None,
                "created_at": _now(),
                "updated_at": _now(),
            }
        )
    if owner_insert_rows:
        op.bulk_insert(users_table, owner_insert_rows)
        op.bulk_insert(
            user_roles_table,
            [
                {
                    "id": uuid.uuid4(),
                    "user_id": row["id"],
                    "role_id": role_ids["platform_owner"],
                    "assigned_by_user_id": row["id"],
                    "is_primary": True,
                    "created_at": _now(),
                }
                for row in owner_insert_rows
            ],
        )

    owner_id = owners_by_email.get("lalitppaunikar26@gmail.com") or next(iter(owners_by_email.values()))
    existing_org_names = {row[0] for row in bind.execute(sa.text("SELECT name FROM organizations")).fetchall()}
    organization_rows = []
    department_rows = []
    organization_product_rows = []
    organization_ids = []
    department_ids_by_org: dict[uuid.UUID, list[uuid.UUID]] = {}
    for index, (name, industry, company_size) in enumerate(ORGANIZATIONS):
        if name in existing_org_names:
            org_id = bind.execute(sa.text("SELECT id FROM organizations WHERE name = :name"), {"name": name}).scalar_one()
            organization_ids.append(org_id)
            continue
        org_id = uuid.uuid4()
        organization_ids.append(org_id)
        organization_rows.append(
            {
                "id": org_id,
                "name": name,
                "logo_url": None,
                "industry": industry,
                "company_size": company_size,
                "gst_number": f"29AACCN{index+1000}Z{index%9}",
                "address": f"{name} campus, Bengaluru",
                "timezone_name": "Asia/Kolkata",
                "country": "India",
                "subscription_name": "Enterprise Recovery" if index % 2 == 0 else "Adaptive Nutrition",
                "renewal_date": date.today() + timedelta(days=90 + index * 15),
                "primary_contact_name": f"{name} Owner",
                "primary_contact_email": f"ops+{_slug(name)}@example.com",
                "status": "ACTIVE",
                "created_by_user_id": owner_id,
                "created_at": _now(),
                "updated_at": _now(),
                "deactivated_at": None,
            }
        )
        department_ids = []
        for department_name in DEPARTMENTS:
            department_id = uuid.uuid4()
            department_ids.append(department_id)
            department_rows.append(
                {
                    "id": department_id,
                    "organization_id": org_id,
                    "name": department_name,
                    "description": f"{department_name} team for {name}",
                    "created_at": _now(),
                    "updated_at": _now(),
                }
            )
        department_ids_by_org[org_id] = department_ids
        organization_product_rows.append(
            {
                "id": uuid.uuid4(),
                "organization_id": org_id,
                "product_id": product_ids["nuetra"],
                "status": "ACTIVE",
                "enabled_at": _now(),
                "disabled_at": None,
            }
        )
        if index % 2 == 0:
            organization_product_rows.append(
                {
                    "id": uuid.uuid4(),
                    "organization_id": org_id,
                    "product_id": product_ids["fiteatsy"],
                    "status": "ACTIVE",
                    "enabled_at": _now(),
                    "disabled_at": None,
                }
            )

    if organization_rows:
        op.bulk_insert(organizations_table, organization_rows)
    if department_rows:
        op.bulk_insert(departments_table, department_rows)
    if organization_product_rows:
        op.bulk_insert(organization_products_table, organization_product_rows)

    def build_people_rows(role_name: str, count: int, prefix: str, start_index: int = 1):
        for idx in range(start_index, start_index + count):
            user_id = uuid.uuid4()
            org_id = organization_ids[(idx - start_index) % len(organization_ids)]
            departments_for_org = department_ids_by_org.get(org_id)
            if not departments_for_org:
                departments_for_org = [
                    row[0]
                    for row in bind.execute(
                        sa.text("SELECT id FROM departments WHERE organization_id = :organization_id ORDER BY name"),
                        {"organization_id": org_id},
                    ).fetchall()
                ]
                department_ids_by_org[org_id] = departments_for_org
            department_id = departments_for_org[(idx - start_index) % len(departments_for_org)]
            primary_product_id = product_ids["fiteatsy"] if idx % 3 == 0 else product_ids["nuetra"]
            yield {
                "user": {
                    "id": user_id,
                    "email": f"{prefix}{idx}@example.com",
                    "password_hash": DEFAULT_PASSWORD_HASH,
                    "company_name": None,
                    "location": "India",
                    "employees": None,
                    "industry": role_name.replace("_", " ").title(),
                    "role_id": role_ids[role_name],
                    "is_active": True,
                    "is_verified": True,
                    "failed_login_attempts": 0,
                    "lock_until": None,
                    "first_name": f"{prefix.title()}",
                    "last_name": f"{idx}",
                    "phone": f"+91-90000{idx:05d}",
                    "avatar_url": None,
                    "status": "ACTIVE",
                    "permissions": [],
                    "company_id": None,
                    "last_login_at": _now(),
                    "deleted_at": None,
                    "created_at": _now(),
                    "updated_at": _now(),
                },
                "membership": {
                    "id": uuid.uuid4(),
                    "user_id": user_id,
                    "organization_id": org_id,
                    "department_id": department_id,
                    "employee_id": f"{role_name[:3].upper()}-{idx:04d}",
                    "package_name": None,
                    "assigned_practitioner_id": None,
                    "assigned_mentor_id": None,
                    "assigned_consultant_id": None,
                    "primary_product_id": primary_product_id,
                    "status": "ACTIVE",
                    "is_verified": True,
                    "tags": [role_name, "seeded"],
                    "created_by_user_id": owner_id,
                    "joined_at": _now(),
                    "created_at": _now(),
                    "updated_at": _now(),
                    "deactivated_at": None,
                },
                "role": {
                    "id": uuid.uuid4(),
                    "user_id": user_id,
                    "role_id": role_ids[role_name],
                    "assigned_by_user_id": owner_id,
                    "is_primary": True,
                    "created_at": _now(),
                },
                "product_access": [
                    {
                        "id": uuid.uuid4(),
                        "user_id": user_id,
                        "product_id": primary_product_id,
                        "organization_id": org_id,
                        "role_id": role_ids[role_name],
                        "status": "ACTIVE",
                        "is_primary": True,
                        "permissions": [],
                        "assigned_by_user_id": owner_id,
                        "created_at": _now(),
                        "updated_at": _now(),
                    }
                ],
                "package_assignment": {
                    "id": uuid.uuid4(),
                    "user_id": user_id,
                    "package_id": package_ids[primary_product_id][idx % len(package_ids[primary_product_id])],
                    "organization_id": org_id,
                    "product_id": primary_product_id,
                    "status": "ACTIVE",
                    "notes": None,
                    "assigned_by_user_id": owner_id,
                    "started_at": _now(),
                    "ended_at": None,
                    "created_at": _now(),
                },
                "service_assignment": {
                    "id": uuid.uuid4(),
                    "user_id": user_id,
                    "service_id": service_ids[primary_product_id][idx % len(service_ids[primary_product_id])],
                    "organization_id": org_id,
                    "product_id": primary_product_id,
                    "status": "ACTIVE",
                    "notes": None,
                    "assigned_by_user_id": owner_id,
                    "started_at": _now(),
                    "ended_at": None,
                    "created_at": _now(),
                },
            }

    user_rows = []
    membership_rows = []
    user_role_rows = []
    product_access_rows = []
    package_assignment_rows = []
    service_assignment_rows = []

    people_specs = [
        ("organization_admin", 25, "orgadmin"),
        ("practitioner", 30, "practitioner"),
        ("mentor", 20, "mentor"),
        ("consultant", 25, "consultant"),
        ("senior_consultant", 10, "seniorconsultant"),
        ("employee", 1000, "employee"),
    ]
    for role_name, count, prefix in people_specs:
        for person in build_people_rows(role_name, count, prefix):
            user_rows.append(person["user"])
            membership_rows.append(person["membership"])
            user_role_rows.append(person["role"])
            product_access_rows.extend(person["product_access"])
            package_assignment_rows.append(person["package_assignment"])
            service_assignment_rows.append(person["service_assignment"])

    if user_rows:
        op.bulk_insert(users_table, user_rows)
        op.bulk_insert(memberships_table, membership_rows)
        op.bulk_insert(user_roles_table, user_role_rows)
        op.bulk_insert(user_product_access_table, product_access_rows)
        op.bulk_insert(user_package_assignments_table, package_assignment_rows)
        op.bulk_insert(user_service_assignments_table, service_assignment_rows)


def downgrade() -> None:
    bind = op.get_bind()
    seeded_domains = [
        "orgadmin",
        "practitioner",
        "mentor",
        "consultant",
        "seniorconsultant",
        "employee",
    ]
    emails = []
    for prefix in seeded_domains:
        rows = bind.execute(sa.text("SELECT email FROM users WHERE email LIKE :pattern"), {"pattern": f"{prefix}%@example.com"}).fetchall()
        emails.extend([row.email for row in rows])
    if emails:
        bind.execute(
            sa.text("DELETE FROM users WHERE email = ANY(:emails)").bindparams(sa.bindparam("emails", expanding=True)),
            {"emails": emails},
        )
    bind.execute(
        sa.text(
            "DELETE FROM organizations WHERE name = ANY(:names)"
        ).bindparams(sa.bindparam("names", expanding=True)),
        {"names": [item[0] for item in ORGANIZATIONS]},
    )
