from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

from app.models import __MODELS__  # noqa: F401
from app.models.base import Base


engine = create_async_engine("sqlite+aiosqlite://")


async def init_db():
  async with engine.begin() as conn:
    await conn.run_sync(Base.metadata.create_all)


@asynccontextmanager
async def get_session():
  session = AsyncSession(engine, expire_on_commit=False)

  try:
    yield session
    await session.commit()
  except:
    await session.rollback()
    raise
  finally:
    await session.close()
