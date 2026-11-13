import json
import logging

import geojson
import pytest

from geomd.models import (
    CodeBlock,
    GeometryBlock,
    Heading,
    HtmlBlock,
    List,
    ListItem,
    Paragraph,
    Text,
)
from geomd.renderers.geojson_renderer import GeoJsonRenderer
from geomd.renderers.geomarkdown_renderer import GeoMarkdownRenderer
from geomd.renderers.html_renderer import GeoHTMLRenderer, _script_safe
from geomd.renderers.json_renderer import JsonRenderer
from geomd.renderers.markdown_renderer import MarkdownRenderer

POINT = {"type": "Point", "coordinates": [2.1527, 41.4145]}


def doc(*nodes):
    return list(nodes)


def heading(level, text):
    return Heading(level=level, children=[Text(raw=text)])


def paragraph(text):
    return Paragraph(children=[Text(raw=text)])


# --- Markdown ---------------------------------------------------------------


def test_markdown_writes_a_geometry_as_a_json_fence():
    output = MarkdownRenderer().render(doc(heading(1, "D"), GeometryBlock(geometry=POINT)))
    assert "```json" in output
    assert '"type": "Point"' in output


def test_markdown_keeps_an_unreadable_geometry_block_verbatim():
    block = GeometryBlock(raw='{"type": "Poin"', error="bad")
    output = MarkdownRenderer().render(doc(block))
    assert '{"type": "Poin"' in output


def test_markdown_writes_a_null_geometry_as_null():
    output = MarkdownRenderer().render(doc(GeometryBlock(geometry=None, raw="null")))
    assert "null" in output


def test_markdown_list_indentation_follows_the_marker():
    nested = List(children=[ListItem(children=[Paragraph(children=[Text(raw="a")])])])
    outer = List(
        ordered=True,
        children=[ListItem(children=[Paragraph(children=[Text(raw="one")]), nested])],
    )
    output = MarkdownRenderer().render(doc(outer))
    assert output.splitlines() == ["1. one", "   - a"]


def test_markdown_keeps_the_start_number():
    listing = List(
        ordered=True,
        start=3,
        children=[
            ListItem(children=[Paragraph(children=[Text(raw="x")])]),
            ListItem(children=[Paragraph(children=[Text(raw="y")])]),
        ],
    )
    assert MarkdownRenderer().render(doc(listing)).splitlines() == ["3. x", "4. y"]


def test_markdown_fence_is_longer_than_the_backticks_inside():
    block = CodeBlock(language="markdown", raw="```\ninner\n```")
    output = MarkdownRenderer().render(doc(block))
    assert output.startswith("````markdown")


def test_markdown_writes_html_blocks_as_they_are():
    output = MarkdownRenderer().render(doc(HtmlBlock(raw="<!--\nfoo:\n-->")))
    assert output == "<!--\nfoo:\n-->\n"


def test_markdown_rejects_an_unknown_block():
    with pytest.raises(ValueError, match="No such block node"):
        MarkdownRenderer().render(doc(ListItem()))


# --- GeoMarkdown ------------------------------------------------------------


def test_geomarkdown_writes_a_geometry_fence():
    output = GeoMarkdownRenderer().render(doc(heading(2, "F"), GeometryBlock(geometry=POINT)))
    assert "```geometry" in output
    assert '"coordinates": [2.1527, 41.4145]' in output


def test_geomarkdown_keeps_a_rejected_block_byte_for_byte():
    raw = '{"type": "Poin", "coordinates":}'
    output = GeoMarkdownRenderer().render(doc(GeometryBlock(raw=raw, error="bad")))
    assert raw in output
    assert "null" not in output


def test_geomarkdown_writes_null_for_a_null_geometry():
    output = GeoMarkdownRenderer().render(doc(GeometryBlock(geometry=None, raw="null")))
    assert "```geometry\nnull\n```" in output


# --- JSON -------------------------------------------------------------------


def test_json_keeps_a_single_item_list_as_a_list():
    listing = List(children=[ListItem(children=[Paragraph(children=[Text(raw="only")])])])
    data = JsonRenderer().render(doc(heading(1, "D"), listing), as_dict=True)
    assert data == {"D": ["only"]}


def test_json_keeps_code_blocks():
    data = JsonRenderer().render(
        doc(heading(1, "D"), CodeBlock(language="python", raw="print(1)")), as_dict=True
    )
    assert data == {"D": "print(1)"}


def test_json_keeps_a_geometry_as_a_dict():
    data = JsonRenderer().render(doc(heading(1, "D"), GeometryBlock(geometry=POINT)), as_dict=True)
    assert data == {"D": POINT}


def test_json_joins_several_paragraphs_with_a_blank_line():
    data = JsonRenderer().render(doc(heading(1, "D"), paragraph("a"), paragraph("b")), as_dict=True)
    assert data == {"D": "a\n\nb"}


def test_json_applies_field_mapping_to_every_sibling():
    metadata = HtmlBlock(raw="<!--\nfield_mapping:\n\t- a: A\n\t- b: B\n-->")
    nodes = doc(
        heading(1, "D"),
        metadata,
        heading(2, "a"),
        paragraph("1"),
        heading(2, "b"),
        paragraph("2"),
    )
    assert JsonRenderer().render(nodes, as_dict=True) == {"D": {"A": "1", "B": "2"}}


def test_json_merges_extra_fields():
    metadata = HtmlBlock(raw="<!--\nextra_fields:\n\t- id: 7\n-->")
    nodes = doc(heading(1, "D"), metadata, heading(2, "a"), paragraph("1"))
    assert JsonRenderer().render(nodes, as_dict=True) == {"D": {"id": "7", "a": "1"}}


def test_json_merges_extra_fields_before_the_sections():
    metadata = HtmlBlock(raw="<!--\nextra_fields:\n\t- id: 7\n-->")
    nodes = doc(heading(1, "D"), metadata, heading(2, "a"), paragraph("1"))
    assert list(JsonRenderer().render(nodes, as_dict=True)["D"]) == ["id", "a"]


def test_json_reports_content_before_the_first_heading(caplog):
    with caplog.at_level(logging.WARNING, logger="geomd"):
        JsonRenderer().render(doc(paragraph("orphan"), heading(1, "D")), as_dict=True)
    assert "before the first heading" in caplog.text


def test_json_does_not_rename_the_members_of_a_geometry(caplog):
    geometry = {"type": "Point", "coordinates": [1, 2]}
    metadata = HtmlBlock(raw="<!--\nfield_mapping:\n\t- type: kind\n-->")
    nodes = doc(heading(1, "D"), metadata, heading(2, "m"), GeometryBlock(geometry=geometry))
    assert JsonRenderer().render(nodes, as_dict=True) == {"D": {"m": geometry}}


# --- GeoJSON ----------------------------------------------------------------


def _render(nodes):
    result = GeoJsonRenderer().render(doc(*nodes), as_dict=True)
    return json.loads(geojson.dumps(result))


def test_geojson_feature_from_a_mapped_geometry():
    metadata = HtmlBlock(raw="<!--\nfield_mapping:\n\t- On map: geometry\n-->")
    nodes = doc(
        heading(1, "Trip"),
        heading(2, "Park"),
        metadata,
        heading(3, "Overview"),
        paragraph("Nice"),
        heading(3, "On map"),
        GeometryBlock(geometry=POINT),
    )
    collection = _render(nodes)
    assert collection["title"] == "Trip"
    feature = collection["features"][0]
    assert feature["title"] == "Park"
    assert feature["geometry"] == POINT
    assert feature["properties"]["Overview"] == "Nice"


def test_geojson_feature_without_a_field_mapping():
    """The spec calls the geometry mapping optional; it used to be required."""
    nodes = doc(
        heading(1, "Trip"),
        heading(2, "Park"),
        heading(3, "Overview"),
        paragraph("Nice"),
        heading(3, "On map"),
        GeometryBlock(geometry=POINT),
    )
    collection = _render(nodes)
    assert len(collection["features"]) == 1
    feature = collection["features"][0]
    assert feature["geometry"] == POINT
    assert feature["properties"]["Overview"] == "Nice"


def test_geojson_title_is_the_top_level_heading():
    nodes = doc(
        heading(1, "Trip"),
        heading(2, "A"),
        GeometryBlock(geometry=POINT),
        heading(2, "B"),
        GeometryBlock(geometry=None),
    )
    assert _render(nodes)["title"] == "Trip"


def test_geojson_keeps_a_null_geometry_feature():
    nodes = doc(heading(1, "Trip"), heading(2, "Nowhere"), GeometryBlock(geometry=None))
    collection = _render(nodes)
    assert len(collection["features"]) == 1
    assert collection["features"][0]["geometry"] is None


def test_geojson_skips_a_section_without_a_geometry(caplog):
    nodes = doc(heading(1, "Trip"), heading(2, "Intro"), paragraph("words"))
    with caplog.at_level(logging.WARNING, logger="geomd"):
        collection = _render(nodes)
    assert collection["features"] == []
    assert "no geometry block" in caplog.text


def test_geojson_handles_two_features():
    nodes = doc(
        heading(1, "Trip"),
        heading(2, "A"),
        GeometryBlock(geometry=POINT),
        heading(2, "B"),
        GeometryBlock(geometry=POINT),
    )
    assert [feature["title"] for feature in _render(nodes)["features"]] == ["A", "B"]


def test_geojson_warns_about_a_second_geometry(caplog):
    nodes = doc(
        heading(1, "Trip"),
        heading(2, "A"),
        heading(3, "one"),
        GeometryBlock(geometry=POINT),
        heading(3, "two"),
        GeometryBlock(geometry=POINT),
    )
    with caplog.at_level(logging.WARNING, logger="geomd"):
        collection = _render(nodes)
    assert len(collection["features"]) == 1
    assert "more than one geometry" in caplog.text


def test_geojson_with_two_top_level_headings_has_no_title():
    nodes = doc(heading(1, "A"), GeometryBlock(geometry=POINT), heading(1, "B"))
    collection = _render(nodes)
    assert collection["title"] == ""
    assert [feature["title"] for feature in collection["features"]] == ["A"]


def test_geojson_output_is_a_real_feature_collection():
    nodes = doc(heading(1, "Trip"), heading(2, "A"), GeometryBlock(geometry=POINT))
    text = GeoJsonRenderer().render(doc(*nodes))
    parsed = json.loads(text)
    assert parsed["type"] == "FeatureCollection"
    assert geojson.loads(text).is_valid


# --- HTML -------------------------------------------------------------------


def test_html_draws_a_map_for_a_geometry():
    from mistune import create_markdown

    output = create_markdown(renderer=GeoHTMLRenderer())(
        "# D\n\n```geometry\n{\"type\": \"Point\", \"coordinates\": [1, 2]}\n```\n"
    )
    assert "geo-map" in output
    assert "L.map" in output


def test_html_escapes_a_script_tag_inside_the_geometry():
    geometry = geojson.loads(json.dumps({
        "type": "Point",
        "coordinates": [1, 2],
        "note": "</script><script>alert(1)</script>",
    }))
    assert "<" not in _script_safe(geometry)


def test_html_falls_back_to_code_for_a_bad_block():
    from mistune import create_markdown

    output = create_markdown(renderer=GeoHTMLRenderer())(
        "# D\n\n```geometry\n{\"type\": \"Poin\"\n```\n"
    )
    assert "L.map" not in output
    assert "Poin" in output


def test_html_declares_english():
    assert 'lang="en"' in GeoHTMLRenderer.HTML_TEMPLATE
