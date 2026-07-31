from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from models.base import Base


engine = create_engine("sqlite://")

Base.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session
