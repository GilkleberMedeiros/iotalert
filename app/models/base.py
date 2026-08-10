from sqlalchemy.orm import DeclarativeBase, Session
from sqlalchemy import select

from app.models.mixins import IDFieldMixin


class Base(DeclarativeBase):
  pass


class BaseModel(Base, IDFieldMixin):
  __abstract__ = True


class ModelRepository[T: BaseModel, CreateData: dict, UpdateData: dict]:
  model: type[T] = None

  def __init__(self, session: Session):
    if self.model is None:
      raise NotImplementedError("Subclasses must define the 'model' attribute.")

    self._session = session

  def create(self, data: list[CreateData] | CreateData) -> list[T] | T:
    if not isinstance(data, list):
      data = [data]

    instances = [self.model(**d) for d in data]

    self._session.add_all(instances)

    return instances if len(instances) > 1 else instances[0]

  def get(self, id) -> T | None:
    model = self.model
    smt = select(model).where(model.id == id)

    result = self._session.scalar(smt)

    return result

  def list(self):
    smt = select(self.model)
    result = self._session.scalars(smt)

    return result

  def update(self, id, data: UpdateData) -> T:
    instance = self._session.get_one(self.model, id)

    for k, v in data.items():
      if k == "id":
        continue

      if k in instance.__table__.columns:
        setattr(instance, k, v)

    self._session.add(instance)
    return instance

  def delete(self, id):
    instance = self._session.get_one(self.model, id)
    self._session.delete(instance)
