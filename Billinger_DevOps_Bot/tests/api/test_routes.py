"""
API Integration & Route Verification Suite.
"""
import unittest
import sys
import json
import urllib.request
import urllib.error
import threading
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from api.server import run_server
from core.configuration.config import Config

class TestAPIRoutes(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.port = 8899
        cls.host = "127.0.0.1"
        cls.base_url = f"http://{cls.host}:{cls.port}"
        
        cls.server_thread = threading.Thread(
            target=run_server,
            kwargs={"host": cls.host, "port": cls.port},
            daemon=True
        )
        cls.server_thread.start()
        time.sleep(0.4)

    def _get(self, path):
        req = urllib.request.Request(f"{self.base_url}{path}")
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))

    def _post(self, path, payload):
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(f"{self.base_url}{path}", data=data, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))

    def test_health_endpoint(self):
        status, body = self._get("/api/health")
        self.assertEqual(status, 200)
        self.assertEqual(body["status"], "OK")
        self.assertIn("system", body)

    def test_catalog_endpoint(self):
        status, body = self._get("/api/learning/catalog")
        self.assertEqual(status, 200)
        self.assertIn("domains", body)

    def test_playground_execution(self):
        status, body = self._post("/api/playground/execute", {"command": "echo test_exec"})
        self.assertEqual(status, 200)
        self.assertIn("status", body)

    def test_ai_routing_endpoint(self):
        status, body = self._post("/api/ai/route", {"workload": "lesson_explanation", "prompt": "Explain Docker multi-stage builds"})
        self.assertEqual(status, 200)
        self.assertIn("content", body)
