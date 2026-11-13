import json

import pytest

from geomd.errors import InvalidGeometryError
from geomd.geometry import GEOMETRY_TYPES, loads_geometry, validate_geometry
from geomd.models import (
    GeometryBlock,
    Heading,
    List,
    Paragraph,
    Text,
    geometry_to_dict,
)

POINT = {"type": "Point", "coordinates": [2.1527, 41.4145]}


def test_node_to_dict_keeps_children_and_drops_empty_values():
    heading = Heading(level=2, children=[Text(raw="Park Güell")])
    assert heading.to_dict() == {
        "type": "heading",
        "level": 2,
        "children": [{"type": "text", "raw": "Park Güell"}],
    }


def test_node_to_dict_omits_an_empty_child_list():
    assert Paragraph().to_dict() == {"type": "paragraph"}


def test_geometry_block_reports_validity():
    block = GeometryBlock(geometry=POINT, raw='{"type": "Point", "coordinates": [2.1527, 41.4145]}')
    assert block.is_valid
    assert block.to_dict()["geometry"] == POINT


def test_geometry_block_keeps_the_reason_it_was_rejected():
    block = GeometryBlock(raw="{", error="invalid geometry block: not valid JSON")
    assert not block.is_valid
    payload = block.to_dict()
    assert payload["raw"] == "{"
    assert "not valid JSON" in payload["error"]


def test_geometry_to_dict_accepts_none_and_objects():
    assert geometry_to_dict(None) is None
    assert geometry_to_dict(POINT) == POINT
    with pytest.raises(TypeError):
        geometry_to_dict(3)


@pytest.mark.parametrize(
    "geometry",
    [
        {"type": "Point", "coordinates": [2.1527, 41.4145]},
        {"type": "Point", "coordinates": [2.1527, 41.4145, 12.0]},
        {"type": "MultiPoint", "coordinates": [[1, 2], [3, 4]]},
        {"type": "LineString", "coordinates": [[1, 2], [3, 4]]},
        {"type": "MultiLineString", "coordinates": [[[1, 2], [3, 4]]]},
        {"type": "Polygon", "coordinates": [[[1, 2], [3, 4], [1, 2]]]},
        {"type": "MultiPolygon", "coordinates": [[[[1, 2], [3, 4], [1, 2]]]]},
        {
            "type": "GeometryCollection",
            "geometries": [{"type": "Point", "coordinates": [1, 2]}],
        },
    ],
)
def test_every_geojson_geometry_type_is_accepted(geometry):
    validate_geometry(geometry)
    assert loads_geometry(json.dumps(geometry)) is not None


def test_every_type_in_the_constant_is_covered():
    assert set(GEOMETRY_TYPES) == {
        "Point",
        "MultiPoint",
        "LineString",
        "MultiLineString",
        "Polygon",
        "MultiPolygon",
        "GeometryCollection",
    }


def test_null_is_read_as_a_missing_geometry():
    assert loads_geometry("null") is None


def test_empty_block_is_an_error():
    with pytest.raises(InvalidGeometryError, match="empty"):
        loads_geometry("  \n ")


def test_broken_json_names_the_column():
    with pytest.raises(InvalidGeometryError) as excinfo:
        loads_geometry('{"type": "Point", "coordinates":}')
    assert "not valid JSON" in excinfo.value.reason
    assert "column" in excinfo.value.reason


def test_unknown_type_is_rejected():
    with pytest.raises(InvalidGeometryError, match="unknown geometry type"):
        validate_geometry({"type": "Poin", "coordinates": [1, 2]})


def test_missing_coordinates_is_rejected():
    with pytest.raises(InvalidGeometryError, match="needs a 'coordinates' member"):
        validate_geometry({"type": "Point"})


def test_non_numeric_position_is_rejected():
    with pytest.raises(InvalidGeometryError, match="must contain numbers"):
        validate_geometry({"type": "Point", "coordinates": ["2.15", 41.4]})


def test_empty_position_is_rejected():
    with pytest.raises(InvalidGeometryError, match="non-empty"):
        validate_geometry({"type": "Point", "coordinates": []})


def test_too_shallow_coordinates_name_the_index():
    with pytest.raises(InvalidGeometryError) as excinfo:
        validate_geometry({"type": "MultiPoint", "coordinates": [1, 2]})
    assert "coordinates[0]" in excinfo.value.reason


def test_geometry_collection_checks_its_members():
    with pytest.raises(InvalidGeometryError) as excinfo:
        validate_geometry({
            "type": "GeometryCollection",
            "geometries": [{"type": "Point"}],
        })
    assert "geometries[0]" in excinfo.value.reason


def test_geometry_collection_needs_a_list():
    with pytest.raises(InvalidGeometryError, match="'geometries' list"):
        validate_geometry({"type": "GeometryCollection"})


def test_a_geometry_must_be_an_object():
    with pytest.raises(InvalidGeometryError, match="JSON object"):
        validate_geometry([1, 2])


def test_list_node_keeps_its_flags():
    node = List(ordered=True, start=3, depth=1)
    assert node.to_dict() == {"type": "list", "ordered": True, "start": 3, "depth": 1}
