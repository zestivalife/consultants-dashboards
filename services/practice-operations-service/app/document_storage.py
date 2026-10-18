from datetime import datetime,timezone
from uuid import uuid4
from app.config import get_settings

class StorageUnavailable(RuntimeError):pass
def _client():
    s=get_settings()
    if not all((s.document_storage_bucket,s.document_storage_access_key,s.document_storage_secret_key)):raise StorageUnavailable("Governed document storage is not configured")
    import boto3
    args={"aws_access_key_id":s.document_storage_access_key,"aws_secret_access_key":s.document_storage_secret_key,"region_name":s.document_storage_region}
    if s.document_storage_endpoint:args["endpoint_url"]=s.document_storage_endpoint
    return boto3.client("s3",**args),s
def new_object_key(tenant_id,document_id,filename):
    suffix=(filename.rsplit('.',1)[-1] if '.' in filename else 'bin').lower()
    return f"external-vault/{tenant_id}/{document_id}/{uuid4().hex}.{suffix}"
def signed_upload(key,content_type):
    client,s=_client();return client.generate_presigned_url("put_object",Params={"Bucket":s.document_storage_bucket,"Key":key,"ContentType":content_type},ExpiresIn=600)
def signed_download(key,filename):
    client,s=_client();return client.generate_presigned_url("get_object",Params={"Bucket":s.document_storage_bucket,"Key":key,"ResponseContentDisposition":f'attachment; filename="{filename}"'},ExpiresIn=300)
