import unittest
from pathlib import Path


class ServiceRoutesTest(unittest.TestCase):
    def test_owner_master_data_routes_to_auth_service(self):
        config_source = Path("app/config.py").read_text()

        self.assertIn(
            '{"prefix": "/api/v1/owner/master-data", "upstream": self.auth_service_url}',
            config_source,
        )


if __name__ == "__main__":
    unittest.main()
