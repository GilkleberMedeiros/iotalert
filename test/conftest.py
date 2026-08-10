from unittest import TestCase
from unittest.mock import patch

from sqlalchemy import create_engine

from app.models import __MODELS__  # noqa: F401
from app.models.base import Base

test_engine = create_engine("sqlite:///:memory:")


class InMemoryDatabaseTestCase(TestCase):
  """
  Fixture that uses an in-memory engine for underlying
  tests instead of default production engine.
  """

  @classmethod
  def setUpClass(cls):
    super().setUpClass()

    cls.patcher = patch("app.db.engine", test_engine)
    cls.mock_engine = cls.patcher.start()
    Base.metadata.create_all(test_engine)

  @classmethod
  def tearDownClass(cls):
    Base.metadata.drop_all(test_engine)
    cls.patcher.stop()
    test_engine.dispose()
    return super().tearDownClass()
