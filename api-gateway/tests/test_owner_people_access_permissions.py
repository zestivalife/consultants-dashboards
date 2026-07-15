import unittest

from app.routers.owner_permissions import required_owner_permissions


class OwnerPeopleAccessPermissionRulesTest(unittest.TestCase):
    def test_package_assignment_requires_package_permission(self):
        permissions = required_owner_permissions(
            "/api/v1/owner/people-access/users/11111111-1111-1111-1111-111111111111/packages",
            "PUT",
        )
        self.assertEqual(permissions, {"packages.manage"})

    def test_service_assignment_requires_service_permission(self):
        permissions = required_owner_permissions(
            "/api/v1/owner/people-access/users/11111111-1111-1111-1111-111111111111/services",
            "PUT",
        )
        self.assertEqual(permissions, {"services.manage"})

    def test_product_assignment_requires_user_edit_permission(self):
        permissions = required_owner_permissions(
            "/api/v1/owner/people-access/users/11111111-1111-1111-1111-111111111111/products",
            "PUT",
        )
        self.assertEqual(permissions, {"users.edit"})

    def test_force_logout_requires_force_logout_permission(self):
        permissions = required_owner_permissions(
            "/api/v1/owner/people-access/users/11111111-1111-1111-1111-111111111111/force-logout",
            "POST",
        )
        self.assertEqual(permissions, {"users.force_logout"})

    def test_session_revoke_requires_force_logout_permission(self):
        permissions = required_owner_permissions(
            "/api/v1/owner/people-access/users/11111111-1111-1111-1111-111111111111/sessions/22222222-2222-2222-2222-222222222222/revoke",
            "POST",
        )
        self.assertEqual(permissions, {"users.force_logout"})

    def test_user_detail_still_requires_read_permission(self):
        permissions = required_owner_permissions(
            "/api/v1/owner/people-access/users/11111111-1111-1111-1111-111111111111",
            "GET",
        )
        self.assertEqual(permissions, {"users.read"})

    def test_invitation_lifecycle_requires_invite_permission(self):
        for action in ("resend", "cancel", "expire"):
            permissions = required_owner_permissions(
                f"/api/v1/owner/people-access/invitations/11111111-1111-1111-1111-111111111111/{action}",
                "POST",
            )
            self.assertEqual(permissions, {"users.invite"})


if __name__ == "__main__":
    unittest.main()
