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

    def test_production_railway_public_urls_route_to_private_dns(self):
        settings = Settings(
            app_env="production",
            jwt_secret_key="test-secret",
            auth_service_url="https://auth-service-production-ef64.up.railway.app",
            profile_service_url="https://profile-service-production-abcd.up.railway.app",
            assessment_service_url="https://assessment-service-production-abcd.up.railway.app",
            scoring_service_url="https://scoring-engine-service-production-abcd.up.railway.app",
            nutrition_service_url="https://nutrition-service-production-abcd.up.railway.app",
        )
        routes = {route["prefix"]: route for route in settings.get_service_routes()}

        self.assertEqual(routes["/api/v1/owner/people-access"]["upstream"], "http://auth-service.railway.internal:8080")
        self.assertEqual(routes["/api/v1/owner/people-access"]["host_header"], "auth-service-production-ef64.up.railway.app")
        self.assertEqual(routes["/api/v1/auth"]["upstream"], "http://auth-service.railway.internal:8080")
        self.assertEqual(routes["/api/v1/auth"]["host_header"], "auth-service-production-ef64.up.railway.app")
        self.assertEqual(routes["/api/v1/profile"]["upstream"], "http://profile-service.railway.internal:8080")
        self.assertEqual(routes["/api/v1/assessments"]["upstream"], "http://assessment-service.railway.internal:8080")
        self.assertEqual(routes["/api/v1/scoring"]["upstream"], "http://scoring-engine-service.railway.internal:8080")
        self.assertEqual(routes["/api/v1/nutrition"]["upstream"], "http://nutrition-service.railway.internal:8080")

    def test_production_railway_private_urls_use_runtime_port(self):
        settings = Settings(
            app_env="production",
            jwt_secret_key="test-secret",
            profile_service_url="http://profile-service.railway.internal",
            assessment_service_url="http://assessment-service.railway.internal",
            scoring_service_url="http://scoring-engine-service.railway.internal",
            nutrition_service_url="http://nutrition-service.railway.internal",
        )
        upstreams = settings.get_service_upstreams()

        self.assertEqual(upstreams["profile-service"], "http://profile-service.railway.internal:8080")
        self.assertEqual(upstreams["assessment-service"], "http://assessment-service.railway.internal:8080")
        self.assertEqual(upstreams["scoring-engine-service"], "http://scoring-engine-service.railway.internal:8080")
        self.assertEqual(upstreams["nutrition-service"], "http://nutrition-service.railway.internal:8080")

    def test_retired_invitation_onboarding_paths_are_not_public(self):
        jwt_source = Path("app/middleware/jwt.py").read_text()

        self.assertNotIn('"/api/v1/auth/register"', jwt_source)
        self.assertNotIn('"/api/v1/auth/verify-otp"', jwt_source)
        self.assertNotIn('"/api/v1/auth/resend-otp"', jwt_source)
        self.assertNotIn('"/api/v1/auth/forgot-password"', jwt_source)
        self.assertNotIn('"/api/v1/onboarding/invitations/validate"', jwt_source)
        self.assertNotIn('"/api/v1/onboarding/invitations/accept"', jwt_source)
        self.assertNotIn('"/api/v1/onboarding/password/setup"', jwt_source)
        self.assertNotIn('"/api/v1/identity/password/create"', jwt_source)

    def test_retired_onboarding_and_identity_routes_are_not_registered(self):
        settings = Settings(auth_service_url="http://auth-service.railway.internal")
        routes = {route["prefix"]: route["upstream"] for route in settings.get_service_routes()}

        self.assertNotIn("/api/v1/onboarding", routes)
        self.assertNotIn("/api/v1/identity", routes)


if __name__ == "__main__":
    unittest.main()
