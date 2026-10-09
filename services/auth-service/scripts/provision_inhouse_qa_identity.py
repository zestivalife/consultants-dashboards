#!/usr/bin/env python3
"""Internal-only governed in-house QA provisioner. Never exposes credentials."""

import argparse
import asyncio
import os
import sys
import uuid
from pathlib import Path

SERVICE_ROOT = Path(__file__).resolve().parents[1]
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

from app.db.session import get_session_factory
from app.services.inhouse_qa_provisioning_service import (
    ProvisionInhouseQaCommand,
    provision_inhouse_qa_identity,
)


async def run(args: argparse.Namespace) -> None:
    password = os.environ.get("FITEATSY_QA_PROVISIONING_PASSWORD")
    if not password:
        raise SystemExit("FITEATSY_QA_PROVISIONING_PASSWORD is required")
    organization_id = uuid.UUID(args.organization_id) if args.organization_id else None
    async with get_session_factory()() as session:
        record = await provision_inhouse_qa_identity(session, ProvisionInhouseQaCommand(
            fixture_key=args.fixture_key,
            canonical_role=args.role,
            email=args.email,
            mobile_number=args.mobile,
            password=password,
            display_name=args.display_name,
            created_by_reference=args.created_by,
            organization_id=organization_id,
        ))
        print(f"fixture={record.fixture_key} status={record.status} auth_identity={record.auth_user_id} application_user={record.fiteatsy_user_id}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture-key", required=True)
    parser.add_argument("--role", required=True)
    parser.add_argument("--email", required=True)
    parser.add_argument("--mobile", required=True)
    parser.add_argument("--display-name", required=True)
    parser.add_argument("--created-by", required=True)
    parser.add_argument("--organization-id")
    asyncio.run(run(parser.parse_args()))


if __name__ == "__main__":
    main()
