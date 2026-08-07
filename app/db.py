from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.models import __MODELS__  # noqa: F401
from app.models.base import Base


engine = create_engine("sqlite://")

Base.metadata.create_all(engine)


def get_session():
  session = Session(engine)

  try:
    yield session
    session.commit()
  except:
    session.rollback()
    raise
  finally:
    session.close()
