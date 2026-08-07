from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column
from sqlalchemy import select


class Base(DeclarativeBase):
  id: Mapped[int] = mapped_column(primary_key=True)


class ModelRepository[T: Base, CreateData: dict, UpdateData: dict]:
  def __init__(self, session: Session):
    self._session = session

  def create(self, data: list[CreateData] | CreateData) -> list[T] | T:
    if not isinstance(data, list):
      data = [data]

    instances = [T(**d) for d in data]

    self._session.add_all(instances)

    return instances if len(instances) > 1 else instances[0]

  def get(self, id) -> T | None:
    smt = select(T).where(T.id == id)

    result = self._session.scalar(smt)

    return result

  def list(self):
    smt = select(T)
    result = self._session.scalars(smt)

    return result

  def update(self, id, data: UpdateData) -> T:
    instance = self._session.get_one(T, id)

    for k, v in data.items():
      if k == "id":
        continue

      if k in instance.__table__.columns:
        setattr(instance, k, v)

    self._session.add(instance)
    return instance

  def delete(self, id):
    instance = self._session.get_one(T, id)
    self._session.delete(instance)
