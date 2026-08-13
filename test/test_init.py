"""
Initialization tests.
"""

from unittest import TestCase
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncEngine

from app.main import app


class TestAppInitTestCase(TestCase):
  def setUp(self):
    self.client = TestClient(app)
    return super().setUp()

  def test_server_ping(self):
    response = self.client.get("/ping")

    self.assertEqual(response.status_code, 200)
    self.assertEqual(response.json()["message"], "pong")

  def test_can_get_db_engine(self):
    from app.db import engine

    self.assertIsInstance(engine, AsyncEngine)
