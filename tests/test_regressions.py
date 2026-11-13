"""Named regressions: every test here failed before the fix beside it."""

import json
import logging

import pytest

import geomd
from geomd.renderers.json_renderer import JsonRenderer

POINT = {"type": "Point", "coordinates": [2.1527, 41.4145]}


def md_with_feature(body: str, geometry: dict | None = POINT) -> str:
    block = "null" if geometry is None else json.dumps(geometry)
    return f"# Trip\n\n## Park\n\n{body}\n\n### On map\n\n```geometry\n{block}\n```\n"


def test_text_after_emphasis_is_no_longer_lost():
    """`_get_children` tested the previous child, so the tail of a sentence vanished."""
    document = md_with_feature("### Overview\n\nA **colorful** park by Gaudi, *very* nice")
    data = geomd.convert(document, "geomd", "json", as_dict=True)
    assert data["Trip"]["Park"]["Overview"] == "A colorful park by Gaudi, very nice"


def test_a_bullet_list_no_longer_raises():
    """Rendering a list item raised `ValueError: No such inline node: paragraph`."""
    document = md_with_feature("### Tags\n\n* red\n* green")
    assert geomd.convert(document, "geomd", "geojson")


def test_a_star_list_is_still_unordered_after_a_round_trip():
    """`bullet != '-'` reported every `*` and `+` list as numbered."""
    document = md_with_feature("### Tags\n\n* red\n* green")
    output = geomd.convert(document, "geomd", "geomd")
    assert "- red" in output
    assert "1. red" not in output


def test_image_alt_and_title_are_not_swapped():
    document = md_with_feature('### Photo\n\n![A cat](cat.png "the cat")')
    output = geomd.convert(document, "geomd", "geomd")
    assert '![A cat](cat.png "the cat")' in output


def test_third_party_geojson_without_a_title_is_accepted():
    """`feature['title']` raised KeyError for every ordinary GeoJSON file."""
    document = json.dumps({
        "type": "FeatureCollection",
        "features": [
            {"type": "Feature", "properties": {"name": "A"}, "geometry": POINT},
        ],
    })
    output = geomd.convert(document, "geojson", "geomd")
    assert "## A" in output


def test_two_features_with_one_title_are_both_kept(caplog):
    """The second feature used to overwrite the first in a dict keyed by title."""
    document = json.dumps({
        "type": "FeatureCollection",
        "features": [
            {"type": "Feature", "title": "Stop", "properties": {"n": 1}, "geometry": POINT},
            {"type": "Feature", "title": "Stop", "properties": {"n": 2}, "geometry": POINT},
        ],
    })
    with caplog.at_level(logging.WARNING, logger="geomd"):
        markdown = geomd.convert(document, "geojson", "geomd")
    assert "## Stop" in markdown
    assert "## Stop (2)" in markdown
    assert "so neither is lost" in caplog.text

    back = geomd.convert(markdown, "geomd", "geojson", as_dict=True)
    assert [feature["properties"]["n"] for feature in back["features"]] == ["1", "2"]


def test_markdown_output_accepts_a_geometry_block():
    """The `md` destination raised `ValueError: No such block node: geometry_block`."""
    document = md_with_feature("### Overview\n\nNice")
    assert "```json" in geomd.convert(document, "geomd", "md")


def test_a_broken_geometry_block_is_not_replaced_by_null():
    """An unreadable block silently rendered as `geometry null` on the way back."""
    document = md_with_feature("### Overview\n\nNice").replace(
        json.dumps(POINT), '{"type": "Poin", "coordinates":}'
    )
    output = geomd.convert(document, "geomd", "geomd")
    assert '{"type": "Poin", "coordinates":}' in output
    assert "```geometry\nnull\n```" not in output


def test_the_console_script_target_exists():
    """`geomd = "geomd:main"` pointed at a function that did not exist."""
    assert callable(geomd.main)


def test_a_feature_needs_no_field_mapping_for_its_geometry():
    """The spec calls the mapping optional, and it was required."""
    document = (
        "# Trip\n\n## Park\n\n### Overview\n\nNice\n\n### On map\n\n"
        '```geometry\n{"type": "Point", "coordinates": [1, 2]}\n```\n'
    )
    collection = geomd.convert(document, "geomd", "geojson", as_dict=True)
    assert len(collection["features"]) == 1
    assert collection["features"][0]["geometry"] == {"type": "Point", "coordinates": [1, 2]}


def test_the_collection_title_is_not_taken_from_a_nested_heading():
    """A feature without geometry used to rename the whole collection `title`."""
    document = "# Trip\n\n## Intro\n\nwords\n\n## Park\n\n### On map\n\n```geometry\nnull\n```\n"
    collection = geomd.convert(document, "geomd", "geojson", as_dict=True)
    assert collection["title"] == "Trip"


def test_a_one_item_list_stays_a_list():
    """`len(values) == 1` on a string made a list of one look like a scalar."""
    document = md_with_feature("### Tags\n\n* red")
    data = geomd.convert(document, "geomd", "json", as_dict=True)
    assert data["Trip"]["Park"]["Tags"] == ["red"]


def test_a_metadata_comment_with_extra_fields_as_a_list_does_not_crash():
    """The GeoJSON `_metadata` form lists names, and `dict.update` raised on it."""
    data = {"a": "1", "_metadata": {"extra_fields": ["a"], "field_mapping": {}}}
    assert JsonRenderer()._map_fields_and_add_extra_fields(data) == {"a": "1"}


def test_unknown_format_is_a_clear_error():
    with pytest.raises(geomd.UnknownFormatError, match="unknown format 'pdf'"):
        geomd.convert("# D\n", "geomd", "pdf")


def test_a_geometry_without_coordinates_is_kept_with_its_reason():
    document = md_with_feature("### Overview\n\nNice").replace(
        json.dumps(POINT), '{"type": "Point"}'
    )
    nodes = geomd.parse(document, "geomd")
    block = [node for node in nodes if isinstance(node, geomd.GeometryBlock)][0]
    assert block.geometry is None
    assert "coordinates" in block.error
