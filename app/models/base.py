from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
  id: Mapped[int] = mapped_column(primary_key=True)


# TODO: Implement Base model repository methods
class ModelRepository[T: Base]:
  pass
