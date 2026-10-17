from app.routers.owner_permissions import required_owner_permissions


def test_external_qa_provisioning_requires_explicit_permission():
    path = "/api/v1/owner/people-access/qa/external-practice"
    assert required_owner_permissions(path, "POST") == {"qa.external_practice.provision"}
    assert required_owner_permissions(path, "GET") == set()
