"""Reading and checking the GeoJSON geometry inside a ``geometry`` block."""

from __future__ import annotations

import json
from typing import Any

import geojson

from .errors import InvalidGeometryError

#: The geometry types of RFC 7946 section 3.
GEOMETRY_TYPES = (
    "Point",
    "MultiPoint",
    "LineString",
    "MultiLineString",
    "Polygon",
    "MultiPolygon",
    "GeometryCollection",
)

#: Leaf shape of each type: number of nesting levels of coordinates.
_COORDINATE_DEPTH = {
    "Point": 0,
    "MultiPoint": 1,
    "LineString": 1,
    "MultiLineString": 2,
    "Polygon": 2,
    "MultiPolygon": 3,
}


def loads_geometry(text: str) -> geojson.GeoJSON | None:
    """Parse the body of a ``geometry`` block and validate it.

    Returns ``None`` for an explicit ``null`` (a feature with no geometry,
    which GeoJSON allows).  Raises :class:`InvalidGeometryError` with the
    reason when the body is not a GeoJSON geometry.
    """
    body = text.strip()
    if not body:
        raise InvalidGeometryError("the block is empty")
    try:
        data = json.loads(body)
    except json.JSONDecodeError as exc:
        raise InvalidGeometryError(f"not valid JSON ({exc.msg} at column {exc.colno})", snippet=body) from exc

    if data is None:
        return None
    validate_geometry(data)
    return geojson.loads(body)


def validate_geometry(data: Any) -> None:
    """Check one geometry object; raise :class:`InvalidGeometryError` if it is not one."""
    if not isinstance(data, dict):
        raise InvalidGeometryError(
            f"a geometry must be a JSON object, got {type(data).__name__}", snippet=json.dumps(data)
        )

    geometry_type = data.get("type")
    if geometry_type not in GEOMETRY_TYPES:
        known = ", ".join(GEOMETRY_TYPES)
        raise InvalidGeometryError(
            f"unknown geometry type {geometry_type!r} (expected one of {known})",
            snippet=json.dumps(data),
        )

    if geometry_type == "GeometryCollection":
        geometries = data.get("geometries")
        if not isinstance(geometries, list):
            raise InvalidGeometryError("GeometryCollection needs a 'geometries' list")
        for index, child in enumerate(geometries):
            try:
                validate_geometry(child)
            except InvalidGeometryError as exc:
                raise InvalidGeometryError(f"geometries[{index}]: {exc.reason}") from exc
        return

    if "coordinates" not in data:
        raise InvalidGeometryError(f"{geometry_type} needs a 'coordinates' member")
    _check_coordinates(data["coordinates"], _COORDINATE_DEPTH[geometry_type], geometry_type)


def _check_coordinates(value: Any, depth: int, geometry_type: str) -> None:
    if depth > 0:
        if not isinstance(value, list):
            raise InvalidGeometryError(
                f"{geometry_type} coordinates must be nested {depth + 1} level(s) deep, "
                f"found {type(value).__name__}"
            )
        for index, child in enumerate(value):
            try:
                _check_coordinates(child, depth - 1, geometry_type)
            except InvalidGeometryError as exc:
                raise InvalidGeometryError(f"coordinates[{index}]: {exc.reason}") from exc
        return

    if not isinstance(value, list) or not value:
        raise InvalidGeometryError(
            f"{geometry_type} position must be a non-empty [longitude, latitude] list"
        )
    for element in value:
        if isinstance(element, bool) or not isinstance(element, (int, float)):
            raise InvalidGeometryError(
                f"{geometry_type} position must contain numbers, found {element!r}"
            )
