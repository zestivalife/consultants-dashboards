from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.otp_verification import OTPVerification


class OTPVerificationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, record: OTPVerification) -> OTPVerification:
        self._session.add(record)
        await self._session.flush()
        return record
