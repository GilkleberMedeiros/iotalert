from unittest import IsolatedAsyncioTestCase
from unittest.mock import patch

from sqlalchemy.ext.asyncio import create_async_engine

from app.models import __MODELS__  # noqa: F401
from app.models.base import Base

test_engine = create_async_engine("sqlite+aiosqlite:///:memory:")


class InMemoryDatabaseTestCase(IsolatedAsyncioTestCase):
  """
  Fixture that uses an in-memory engine for underlying
  tests instead of default production engine.
  """

  async def asyncSetUp(self):
    await super().asyncSetUp()

    self.patcher = patch("app.db.engine", test_engine)
    self.mock_engine = self.patcher.start()
    async with test_engine.begin() as conn:
      await conn.run_sync(Base.metadata.create_all)

  async def asyncTearDown(self):
    async with test_engine.begin() as conn:
      await conn.run_sync(Base.metadata.drop_all)
    self.patcher.stop()
    await test_engine.dispose()
    return await super().asyncTearDown()
