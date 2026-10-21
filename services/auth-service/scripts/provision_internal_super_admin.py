#!/usr/bin/env python3
"""Provision one Internal Super Admin without exposing the temporary password."""

import argparse
import asyncio
from getpass import getpass
import sys
import uuid
from pathlib import Path

SERVICE_ROOT = Path(__file__).resolve().parents[1]
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

from app.db.session import get_session_factory
from app.services.internal_admin_provisioning_service import (
    ProvisionInternalSuperAdminCommand,
    provision_internal_super_admin,
)


async def run(args: argparse.Namespace) -> None:
    temporary_password = getpass("Temporary password: ")
    confirmation = getpass("Confirm temporary password: ")
    if temporary_password != confirmation:
        raise SystemExit("Password confirmation does not match")

    async with get_session_factory()() as session:
        try:
            user = await provision_internal_super_admin(
                session,
                ProvisionInternalSuperAdminCommand(
                    email=args.email,
                    first_name=args.first_name,
                    last_name=args.last_name,
                    phone=args.phone,
                    temporary_password=temporary_password,
                    operator_user_id=uuid.UUID(args.operator_user_id),
                ),
            )
            await session.commit()
        except Exception:
            await session.rollback()
            raise
    print(
        "Internal Super Admin provisioned; mandatory first-login password change is active "
        f"for user_id={user.id}"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--email", required=True)
    parser.add_argument("--first-name", required=True)
    parser.add_argument("--last-name", required=True)
    parser.add_argument("--phone", required=True)
    parser.add_argument("--operator-user-id", required=True)
    asyncio.run(run(parser.parse_args()))


if __name__ == "__main__":
    main()
