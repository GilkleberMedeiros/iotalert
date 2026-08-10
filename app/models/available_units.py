from typing import Callable, TypedDict


_validate_func_docstring = (
  "Validates unit value. Raises ValueError if invalid. Ex.: 361° (degrees) is invalid"
)
_format_func_docstring = "Format unit value to for presentation. Ex.: 32 -> 32 °C"


class UnitData(TypedDict):
  validate: Callable[[float], None]
  format: Callable[[float], str]


UNITS: dict[str, UnitData] = {}


# ==================================
#         TEMPERATURE UNITS
# ==================================

UNITS["celsius"] = {
  "validate": lambda value: ...,
  "format": lambda value: f"{value} °C",
}

UNITS["kelvin"] = {
  "validate": lambda value: ...,
  "format": lambda value: f"{value} K",
}

UNITS["fahrenheit"] = {
  "validate": lambda value: ...,
  "format": lambda value: f"{value} °F",
}


# ==================================
#         MASS/WEIGHT UNITS
# ==================================

UNITS["kilogram"] = {
  "validate": lambda value: ...,
  "format": lambda value: f"{value} kg",
}

UNITS["gram"] = {"validate": lambda value: ..., "format": lambda value: f"{value} g"}

UNITS["pound"] = {"validate": lambda value: ..., "format": lambda value: f"{value} lb"}

UNITS["ton"] = {"validate": lambda value: ..., "format": lambda value: f"{value} t"}


# ==================================
#         PRESSURE UNITS
# ==================================

UNITS["pascal"] = {"validate": lambda value: ..., "format": lambda value: f"{value} Pa"}

UNITS["bar"] = {"validate": lambda value: ..., "format": lambda value: f"{value} bar"}

UNITS["psi"] = {"validate": lambda value: ..., "format": lambda value: f"{value} psi"}

UNITS["l-min"] = {
  "validate": lambda value: ...,
  "format": lambda value: f"{value} L/min",
}

UNITS["m3-hour"] = {
  "validate": lambda value: ...,
  "format": lambda value: f"{value} m³/h",
}


# ==================================
#         ELETRICAL UNITS
# ==================================

UNITS["kilowatt-hour"] = {
  "validate": lambda value: ...,
  "format": lambda value: f"{value} kWh",
}

UNITS["kilowatt"] = {
  "validate": lambda value: ...,
  "format": lambda value: f"{value} kW",
}

UNITS["volt"] = {
  "validate": lambda value: ...,
  "format": lambda value: f"{value} V",
}

UNITS["ampere"] = {
  "validate": lambda value: ...,
  "format": lambda value: f"{value} A",
}


# ==================================
#         DISTANCE UNITS
# ==================================

UNITS["millimeter"] = {
  "validate": lambda value: ...,
  "format": lambda value: f"{value} mm",
}

UNITS["meter"] = {
  "validate": lambda value: ...,
  "format": lambda value: f"{value} m",
}


# ==================================
#         LOGICAL/UTILS UNITS
# ==================================


def validate_degree(value: float):
  if value < 0 or value > 360:
    raise ValueError(
      f"Degree must be in an interval between 0° to 360°. Current value: {value}"
    )


validate_degree.__doc__ = _validate_func_docstring

UNITS["degree"] = {
  "validate": validate_degree,
  "format": lambda value: f"{value}°",
}

UNITS["percentage"] = {
  "validate": lambda value: ...,
  "format": lambda value: f"{value}%",
}

UNITS["hertz"] = {
  "validate": lambda value: ...,
  "format": lambda value: f"{value} Hz",
}


def __add_docstring(item: tuple):
  v = item[1]
  v["validate"].__doc__ = _validate_func_docstring
  v["format"].__doc__ = _format_func_docstring

  return (item[0], v)


UNITS = dict(map(__add_docstring, UNITS.items()))
