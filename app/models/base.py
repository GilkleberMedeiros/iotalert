from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.ext.asyncio import AsyncSession, AsyncAttrs
from sqlalchemy import select

from app.models.mixins import IDFieldMixin


class Base(AsyncAttrs, DeclarativeBase):
  pass


class BaseModel(Base, IDFieldMixin):
  __abstract__ = True


class ModelRepository[T: BaseModel, CreateData: dict, UpdateData: dict]:
  model: type[T] = None

  def __init__(self, session: AsyncSession):
    if self.model is None:
      raise NotImplementedError("Subclasses must define the 'model' attribute.")

    self._session = session

  async def create(self, data: list[CreateData] | CreateData) -> list[T] | T:
    if not isinstance(data, list):
      data = [data]

    instances = [self.model(**d) for d in data]

    self._session.add_all(instances)

    return instances if len(instances) > 1 else instances[0]

  async def get(self, id) -> T | None:
    model = self.model
    smt = select(model).where(model.id == id)

    result = await self._session.scalar(smt)

    return result

  async def list(self):
    smt = select(self.model)
    result = await self._session.scalars(smt)

    return result

  async def update(self, id, data: UpdateData) -> T:
    instance = await self._session.get_one(self.model, id)

    for k, v in data.items():
      if k == "id":
        continue

      if k in instance.__table__.columns:
        setattr(instance, k, v)

    self._session.add(instance)
    return instance

  async def delete(self, id):
    instance = await self._session.get_one(self.model, id)
    await self._session.delete(instance)
