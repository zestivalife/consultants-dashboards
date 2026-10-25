from types import SimpleNamespace

from app import document_storage


class PresignRecorder:
    def __init__(self):
        self.params = None

    def generate_presigned_url(self, operation, *, Params, ExpiresIn):
        self.params = Params
        assert operation == "put_object"
        assert ExpiresIn == 600
        return "https://isolated-storage.invalid/upload"


def test_signed_upload_does_not_sign_content_length(monkeypatch):
    client = PresignRecorder()
    settings = SimpleNamespace(document_storage_bucket="isolated-bucket")
    monkeypatch.setattr(document_storage, "_client", lambda: (client, settings))

    result = document_storage.signed_upload("tenant/document/file.pdf", "application/pdf", 128)

    assert result == "https://isolated-storage.invalid/upload"
    assert client.params == {
        "Bucket": "isolated-bucket",
        "Key": "tenant/document/file.pdf",
        "ContentType": "application/pdf",
    }
