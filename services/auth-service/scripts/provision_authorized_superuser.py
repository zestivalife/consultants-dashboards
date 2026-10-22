#!/usr/bin/env python3
"""Provision one authorised superuser without emitting any credential."""

import argparse
import asyncio
import sys
import uuid
from pathlib import Path

SERVICE_ROOT = Path(__file__).resolve().parents[1]
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

from app.db.session import get_session_factory
from app.services.superuser_provisioning_service import (
    ProvisionSuperuserCommand,
    provision_authorized_superuser,
)


async def run(args: argparse.Namespace) -> None:
    async with get_session_factory()() as session:
        result = await provision_authorized_superuser(
            session,
            ProvisionSuperuserCommand(
                operator_user_id=uuid.UUID(args.operator_user_id),
                invitation_id=uuid.UUID(args.invitation_id),
                email=args.email,
                mobile=args.mobile,
                first_name=args.first_name,
                last_name=args.last_name,
            ),
        )
    print(
        " ".join(
            (
                f"user_id={result.user_id}",
                f"role={result.role}",
                f"status={result.status}",
                f"must_change_password={str(result.must_change_password).lower()}",
                f"invitation_status={result.invitation_status}",
                "credential_exposure=none",
            )
        )
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--operator-user-id", required=True)
    parser.add_argument("--invitation-id", required=True)
    parser.add_argument("--email", required=True)
    parser.add_argument("--mobile", required=True)
    parser.add_argument("--first-name", required=True)
    parser.add_argument("--last-name", required=True)
    asyncio.run(run(parser.parse_args()))


if __name__ == "__main__":
    main()
