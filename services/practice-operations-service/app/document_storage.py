from pathlib import Path
from uuid import uuid4

from app.config import get_settings

MAX_DOCUMENT_BYTES = 50 * 1024 * 1024
ALLOWED_CONTENT_TYPES = frozenset({
    "application/pdf", "image/jpeg", "image/png", "text/plain", "text/csv",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
})
EXTENSIONS_BY_TYPE = {
    "application/pdf": {".pdf"}, "image/jpeg": {".jpg", ".jpeg"},
    "image/png": {".png"}, "text/plain": {".txt"}, "text/csv": {".csv"},
    "application/msword": {".doc"},
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": {".docx"},
    "application/vnd.ms-excel": {".xls"},
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": {".xlsx"},
}

class StorageUnavailable(RuntimeError):
    pass

class InvalidDocument(ValueError):
    pass

def _client():
    settings = get_settings()
    if not all((settings.document_storage_bucket, settings.document_storage_access_key,
                settings.document_storage_secret_key)):
        raise StorageUnavailable("Governed document storage is not configured")
    import boto3
    args = {"aws_access_key_id": settings.document_storage_access_key,
            "aws_secret_access_key": settings.document_storage_secret_key,
            "region_name": settings.document_storage_region}
    if settings.document_storage_endpoint:
        args["endpoint_url"] = settings.document_storage_endpoint
    return boto3.client("s3", **args), settings

def validate_document(filename: str, content_type: str, size_bytes: int) -> str:
    clean_name = Path(filename).name.strip()
    if not clean_name or clean_name in {".", ".."}:
        raise InvalidDocument("A safe filename is required")
    if size_bytes <= 0:
        raise InvalidDocument("Empty documents are not allowed")
    if size_bytes > MAX_DOCUMENT_BYTES:
        raise InvalidDocument("Document exceeds the 50 MB limit")
    mime = content_type.lower().split(";", 1)[0].strip()
    if mime not in ALLOWED_CONTENT_TYPES:
        raise InvalidDocument("Document content type is not allowed")
    if Path(clean_name).suffix.lower() not in EXTENSIONS_BY_TYPE[mime]:
        raise InvalidDocument("Document filename extension does not match its content type")
    return clean_name

def new_object_key(tenant_id, document_id, version_id, filename):
    return f"external-vault/{tenant_id}/{document_id}/{version_id}/{uuid4().hex}{Path(filename).suffix.lower()}"

def signed_upload(key, content_type, size_bytes):
    client, settings = _client()
    return client.generate_presigned_url("put_object", Params={"Bucket": settings.document_storage_bucket,
        "Key": key, "ContentType": content_type}, ExpiresIn=600)

def signed_download(key, filename):
    client, settings = _client()
    safe_name = Path(filename).name.replace('"', "")
    return client.generate_presigned_url("get_object", Params={"Bucket": settings.document_storage_bucket,
        "Key": key, "ResponseContentDisposition": f'attachment; filename="{safe_name}"'}, ExpiresIn=300)

def signed_view(key, content_type):
    client, settings = _client()
    return client.generate_presigned_url("get_object", Params={"Bucket": settings.document_storage_bucket,
        "Key": key, "ResponseContentType": content_type}, ExpiresIn=300)

def verify_uploaded_object(key, expected_type, expected_size, expected_checksum=None):
    client, settings = _client()
    try:
        metadata = client.head_object(Bucket=settings.document_storage_bucket, Key=key)
    except Exception as exc:
        raise InvalidDocument("Uploaded object could not be verified") from exc
    actual_size = int(metadata.get("ContentLength", -1))
    actual_type = str(metadata.get("ContentType", "")).lower().split(";", 1)[0]
    if actual_size != expected_size or actual_type != expected_type.lower().split(";", 1)[0]:
        raise InvalidDocument("Uploaded object metadata does not match the declared document")
    checksum = metadata.get("ChecksumSHA256")
    if expected_checksum and checksum and checksum != expected_checksum:
        raise InvalidDocument("Uploaded object checksum does not match")
    return {"size_bytes": actual_size, "content_type": actual_type}
