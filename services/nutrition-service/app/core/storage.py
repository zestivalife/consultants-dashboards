import os
import uuid
from pathlib import Path

from fastapi import UploadFile

from app.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)

ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


async def save_upload(file: UploadFile, user_id: uuid.UUID) -> str:
    ext = Path(file.filename or "file").suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError(f"Unsupported file type: {ext}. Allowed: {', '.join(ALLOWED_EXTENSIONS)}")

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise ValueError("File exceeds 10 MB limit")

    settings = get_settings()
    filename = f"{user_id}/{uuid.uuid4().hex}{ext}"

    if settings.upload_backend == "s3":
        return await _upload_s3(settings, filename, content, file.content_type)

    return await _save_local(settings, filename, content)


async def _save_local(settings, filename: str, content: bytes) -> str:
    dest = Path(settings.upload_local_dir) / filename
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(content)
    logger.info("file_saved_local", path=str(dest))
    return str(dest)


async def _upload_s3(settings, filename: str, content: bytes, content_type: str | None) -> str:
    import boto3

    session = boto3.session.Session()
    client_kwargs = {
        "aws_access_key_id": settings.s3_access_key,
        "aws_secret_access_key": settings.s3_secret_key,
        "region_name": settings.s3_region,
    }
    if settings.s3_endpoint_url:
        client_kwargs["endpoint_url"] = settings.s3_endpoint_url

    s3 = session.client("s3", **client_kwargs)
    s3.put_object(
        Bucket=settings.s3_bucket,
        Key=filename,
        Body=content,
        ContentType=content_type or "application/octet-stream",
    )
    url = f"https://{settings.s3_bucket}.s3.{settings.s3_region}.amazonaws.com/{filename}"
    if settings.s3_endpoint_url:
        url = f"{settings.s3_endpoint_url}/{settings.s3_bucket}/{filename}"
    logger.info("file_uploaded_s3", key=filename)
    return url
