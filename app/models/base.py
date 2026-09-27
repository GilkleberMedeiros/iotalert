from typing import Iterable, NotRequired, TypedDict

from sqlalchemy.orm import DeclarativeBase, selectinload
from sqlalchemy.ext.asyncio import AsyncSession, AsyncAttrs
from sqlalchemy import select, Select

from app.models.mixins import IDFieldMixin


class Base(AsyncAttrs, DeclarativeBase):
  pass


class BaseModel(Base, IDFieldMixin):
  __abstract__ = True


class ListPagination(TypedDict):
  limit: NotRequired[int]
  offset: NotRequired[int]


class ModelRepository[T: BaseModel, CreateData: dict, UpdateData: dict]:
  model: type[T] = None
  FORBID_ID_FIELD_ON_UPDATE: bool = True

  def __init__(self, session: AsyncSession):
    if self.model is None:
      raise NotImplementedError("Subclasses must define the 'model' attribute.")

    self._session = session

  async def create(self, data: list[CreateData] | CreateData) -> list[T] | T:
    if not isinstance(data, list):
      data = [data]

    def f(d: CreateData):
      """Filter forbiden fields on creation."""
      return dict(
        filter(lambda pair: pair[0] not in self.FORBIDEN_CREATE_FIELDS, d.items())
      )

    instances = [self.model(**f(d)) for d in data]

    self._session.add_all(instances)

    return instances if len(instances) > 1 else instances[0]

  async def get(self, id, preload_related: Iterable[BaseModel] = ...) -> T | None:
    model = self.model
    smt = select(model).where(model.id == id)

    if preload_related is not ...:
      smt = self._preload_related(smt, preload_related)

    result = await self._session.scalar(smt)

    return result

  async def list(
    self, pagination: ListPagination = ..., preload_related: Iterable[BaseModel] = ...
  ):
    smt = select(self.model)

    if preload_related is not ...:
      smt = self._preload_related(smt, preload_related)

    if pagination is not ...:
      offset = pagination.get("offset", -1)
      limit = pagination.get("limit", -1)

      smt = smt.offset(offset) if offset >= 0 else smt
      smt = smt.limit(limit) if limit >= 0 else smt

    result = await self._session.scalars(smt)

    return result

  async def update(self, id, data: UpdateData) -> T:
    instance = await self._session.get_one(self.model, id)

    for k, v in data.items():
      if k in self.FORBIDEN_UPDATE_FIELDS:
        continue

      if k in instance.__table__.columns:
        setattr(instance, k, v)

    self._session.add(instance)
    return instance

  async def delete(self, id):
    instance = await self._session.get_one(self.model, id)
    await self._session.delete(instance)

  @staticmethod
  def _preload_related(smt: Select, preload_list: Iterable[BaseModel]):
    preload = set(preload_list)
    for p in preload:
      smt = smt.options(selectinload(p))

    return smt

  @property
  def FORBIDEN_CREATE_FIELDS(self) -> set[str]:
    return {}

  @property
  def FORBIDEN_UPDATE_FIELDS(self) -> set[str]:
    if self.FORBID_ID_FIELD_ON_UPDATE:
      return {"id"}

    return {}
