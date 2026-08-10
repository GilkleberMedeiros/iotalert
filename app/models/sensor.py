import re
import enum
from typing import TypedDict

from sqlalchemy import String, Enum
from sqlalchemy.orm import Mapped, mapped_column, validates

from app.models.base import BaseModel, ModelRepository
from app.models.mixins import CreatedAtFieldMixin
from app.models.available_units import UNITS


UNITS_CHOICES = UNITS.keys()

UnitsEnum = enum.Enum("UnitsEnum", [c for c in UNITS_CHOICES])


class Sensor(BaseModel, CreatedAtFieldMixin):
  __tablename__ = "sensor"

  presentation_name: Mapped[str] = mapped_column(String(255))
  key_name: Mapped[str] = mapped_column(String(255), unique=True, index=True)
  unit: Mapped[enum.Enum] = mapped_column(Enum(UnitsEnum), nullable=False)

  @validates("presentation_name", "key_name")
  def validate_non_empty_string(self, key, value):
    regex = r"^[0-9a-zA-Z\_\.\:]{1,}$"
    if not isinstance(value, str) or not value.strip():
      raise ValueError(f"{key} must be a non-empty string.")

    if key == "key_name" and re.fullmatch(regex, value) is None:
      raise ValueError(
        "key_name must only contains numbers, characters (lower or uppercase)"
        + " and one of these ('_', '.', ':')."
      )

    return value

  @validates("unit")
  def validate_unit_field(self, key, value):
    v = value.strip()
    if v not in set(UNITS_CHOICES):
      raise ValueError("unit should be one of unit choices. Given unit is invalid!")

    return value


class CreateSensorData(TypedDict):
  presentation_name: str
  key_name: str
  unit: str


class UpdateSensorData(TypedDict, total=False):
  presentation_name: str
  key_name: str
  unit: str


class SensorRepository(ModelRepository[Sensor, CreateSensorData, UpdateSensorData]):
  model = Sensor
