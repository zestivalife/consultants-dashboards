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


if __name__ == "__main__":
    unittest.main()
