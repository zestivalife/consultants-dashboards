from app.main import app


def test_document_download_route_precedes_generic_document_action():
    paths = [route.path for route in app.routes if "documents/{document_id}" in route.path]

    assert paths.index("/api/v1/practice-operations/documents/{document_id}/download") < paths.index(
        "/api/v1/practice-operations/documents/{document_id}/{action}"
    )
