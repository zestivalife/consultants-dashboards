import unittest
from pathlib import Path

from app.config import Settings


class ServiceRoutesTest(unittest.TestCase):
    def test_owner_master_data_routes_to_auth_service(self):
        settings = Settings(auth_service_url="http://auth-service.railway.internal")
        routes = {route["prefix"]: route["upstream"] for route in settings.get_service_routes()}

        self.assertEqual(routes["/api/v1/owner/master-data"], "http://auth-service.railway.internal:8001")

    def test_owner_master_data_auth_is_delegated_to_auth_service(self):
        jwt_source = Path("app/middleware/jwt.py").read_text()

        self.assertIn('"/api/v1/owner/master-data"', jwt_source)

    def test_onboarding_routes_to_auth_service(self):
        settings = Settings(auth_service_url="http://auth-service.railway.internal")
        routes = {route["prefix"]: route["upstream"] for route in settings.get_service_routes()}

        self.assertEqual(routes["/api/v1/onboarding"], "http://auth-service.railway.internal:8001")

    def test_identity_routes_to_auth_service(self):
        settings = Settings(auth_service_url="http://auth-service.railway.internal")
        routes = {route["prefix"]: route["upstream"] for route in settings.get_service_routes()}

        self.assertEqual(routes["/api/v1/identity"], "http://auth-service.railway.internal:8001")

    def test_production_railway_public_urls_route_to_private_dns(self):
        settings = Settings(
            app_env="production",
            jwt_secret_key="test-secret",
            auth_service_url="https://auth-service-production-ef64.up.railway.app",
        )
        routes = {route["prefix"]: route["upstream"] for route in settings.get_service_routes()}

        self.assertEqual(routes["/api/v1/owner/people-access"], "http://auth-service.railway.internal:8001")
        self.assertEqual(routes["/api/v1/auth"], "http://auth-service.railway.internal:8001")

    def test_invitation_onboarding_paths_are_public(self):
        jwt_source = Path("app/middleware/jwt.py").read_text()

        self.assertIn('"/api/v1/onboarding/invitations/validate"', jwt_source)
        self.assertIn('"/api/v1/onboarding/invitations/accept"', jwt_source)
        self.assertIn('"/api/v1/onboarding/password/setup"', jwt_source)
        self.assertIn('"/api/v1/identity/password/create"', jwt_source)


if __name__ == "__main__":
    unittest.main()
