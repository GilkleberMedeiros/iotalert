from pydantic import BaseModel


class PaginationParams(BaseModel):
  limit: int = -1
  offset: int = -1
