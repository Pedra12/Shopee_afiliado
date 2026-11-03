import os
import tempfile
import unittest
from pathlib import Path

from starlette.testclient import TestClient


class DashboardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        os.environ["SHOPEE_MODE"] = "fixture"
        os.environ["SHOPEE_APP_DB"] = str(Path(cls.temp.name) / "dashboard.sqlite3")
        os.environ.pop("SHOPEE_APP_ID", None)
        os.environ.pop("SHOPEE_APP_SECRET", None)
        from app import app
        cls.client_context = TestClient(app)
        cls.client = cls.client_context.__enter__()

    @classmethod
    def tearDownClass(cls):
        cls.client_context.__exit__(None, None, None)
        cls.temp.cleanup()
        os.environ.pop("SHOPEE_MODE", None)
        os.environ.pop("SHOPEE_APP_DB", None)

    def test_home_page_is_mobile_dashboard(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Shopee Garimpo", response.text)

    def test_status_explicitly_reports_synthetic_mode(self):
        response = self.client.get("/api/status")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["mode"], "fixture")
        self.assertTrue(payload["synthetic"])

    def test_search_returns_products_and_records_first_observation(self):
        response = self.client.post("/api/search", json={"keyword": "luminária", "sort_type": 2})
        self.assertEqual(response.status_code, 200, response.text)
        payload = response.json()
        self.assertTrue(payload["synthetic"])
        self.assertEqual(len(payload["data"]["offers"]), 2)
        self.assertEqual(payload["data"]["offers"][0]["trend_signal"], "collecting_history")

    def test_repeated_search_calculates_only_comparable_sales_delta(self):
        body = {"keyword": "luminária", "sort_type": 2}
        first = self.client.post("/api/search", json=body).json()
        second = self.client.post("/api/search", json=body).json()
        self.assertIsNone(first["data"]["offers"][0]["sales_change_since_last_scan"])
        self.assertEqual(second["data"]["offers"][0]["sales_change_since_last_scan"], "0")
        self.assertEqual(second["data"]["offers"][0]["trend_signal"], "stable")

    def test_empty_keyword_is_rejected(self):
        response = self.client.post("/api/search", json={"keyword": " "})
        self.assertEqual(response.status_code, 400)


if __name__ == "__main__":
    unittest.main()
