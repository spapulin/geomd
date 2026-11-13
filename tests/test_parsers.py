import json

import pytest

from geomd.errors import InvalidDocumentError
from geomd.models import (
    CodeBlock,
    Formatting,
    GeometryBlock,
    Heading,
    HtmlBlock,
    Image,
    Link,
    List,
    ListItem,
    Paragraph,
    Text,
)
from geomd.parsers.geojson_parser import UNTITLED, GeoJsonParser
from geomd.parsers.geomarkdown_parser import GeoMarkdownParser
from geomd.parsers.json_parser import JsonParser
from geomd.parsers.markdown_parser import MarkdownParser

POINT = {"type": "Point", "coordinates": [2.1527, 41.4145]}


def flatten(node) -> str:
    if isinstance(node, Text):
        return node.raw
    return "".join(flatten(child) for child in getattr(node, "children", []))


def text_of(nodes) -> list[str]:
    return [flatten(node) for node in nodes]


# --- Markdown ---------------------------------------------------------------


def test_heading_level_and_text():
    nodes = MarkdownParser().parse("### On map\n")
    assert isinstance(nodes[0], Heading)
    assert nodes[0].level == 3
    assert flatten(nodes[0]) == "On map"


def test_emphasis_keeps_the_words_after_it():
    """A paragraph used to stop at the first inline token with no node."""
    nodes = MarkdownParser().parse("A **colorful** park by Gaudi, *very* nice\n")
    paragraph = nodes[0]
    assert flatten(paragraph) == "A colorful park by Gaudi, very nice"
    formatting = [child for child in paragraph.children if isinstance(child, Formatting)]
    assert [node.markup for node in formatting] == ["**", "*"]


def test_inline_code_survives():
    assert text_of(MarkdownParser().parse("a `code` b\n")) == ["a code b"]


def test_hard_break_keeps_both_lines():
    nodes = MarkdownParser().parse("a  \nb\n")
    assert flatten(nodes[0]) == "a  \nb"


def test_unordered_star_list_is_not_ordered():
    nodes = MarkdownParser().parse("* red\n* green\n")
    assert isinstance(nodes[0], List)
    assert nodes[0].ordered is False


def test_unordered_plus_list_is_not_ordered():
    assert MarkdownParser().parse("+ a\n")[0].ordered is False


def test_ordered_list_keeps_its_start():
    listing = MarkdownParser().parse("3. x\n4. y\n")[0]
    assert listing.ordered is True
    assert listing.start == 3


def test_nested_list_stays_below_its_item():
    listing = MarkdownParser().parse("* a\n  * b\n")[0]
    item = listing.children[0]
    assert isinstance(item, ListItem)
    assert isinstance(item.children[0], Paragraph)
    assert isinstance(item.children[1], List)


def test_image_alt_and_title_are_not_swapped():
    image = MarkdownParser().parse('![A cat](cat.png "the cat")\n')[0].children[0]
    assert isinstance(image, Image)
    assert (image.url, image.alt, image.title) == ("cat.png", "A cat", "the cat")


def test_link_text_and_url():
    link = MarkdownParser().parse("[the docs](https://example.com)\n")[0].children[0]
    assert isinstance(link, Link)
    assert (link.url, link.title) == ("https://example.com", "the docs")


def test_fenced_code_keeps_language_and_drops_the_trailing_newline():
    block = MarkdownParser().parse("```python\nprint(1)\n```\n")[0]
    assert isinstance(block, CodeBlock)
    assert block.language == "python"
    assert block.raw == "print(1)"


def test_html_comment_is_an_html_block():
    block = MarkdownParser().parse("<!--\nfoo:\n\t- a: b\n-->\n")[0]
    assert isinstance(block, HtmlBlock)
    assert block.raw.startswith("<!--")


def test_thematic_break_is_not_dropped():
    assert text_of(MarkdownParser().parse("---\n")) == ["---"]


def test_block_quote_keeps_its_text():
    assert text_of(MarkdownParser().parse("> quoted words\n")) == ["quoted words"]


def test_blank_lines_do_not_become_nodes():
    nodes = MarkdownParser().parse("\n\n# a\n\n\n# b\n\n")
    assert [node.level for node in nodes] == [1, 1]


# --- GeoMarkdown ------------------------------------------------------------


def test_geometry_block_becomes_a_geometry_node():
    nodes = GeoMarkdownParser().parse('# D\n\n```geometry\n{"type": "Point"}\n```\n'.replace(
        '{"type": "Point"}', json.dumps(POINT)
    ))
    block = nodes[1]
    assert isinstance(block, GeometryBlock)
    assert block.geometry["type"] == "Point"
    assert block.is_valid


def test_null_geometry_is_kept_as_an_explicit_null():
    block = GeoMarkdownParser().parse("# D\n\n```geometry\nnull\n```\n")[1]
    assert isinstance(block, GeometryBlock)
    assert block.geometry is None
    assert block.is_valid


def test_invalid_geometry_keeps_the_original_text():
    raw = '{"type": "Poin", "coordinates":}'
    block = GeoMarkdownParser().parse(f"# D\n\n```geometry\n{raw}\n```\n")[1]
    assert block.geometry is None
    assert block.raw == raw
    assert "not valid JSON" in block.error


def test_a_json_block_is_not_a_geometry_block():
    block = GeoMarkdownParser().parse('# D\n\n```json\n{"type": "Point"}\n```\n')[1]
    assert isinstance(block, CodeBlock)


def test_geometry_inside_a_list_item_is_upgraded():
    nodes = GeoMarkdownParser().parse("* item\n\n  ```geometry\nnull\n```\n")
    item = nodes[0].children[0]
    assert any(isinstance(child, GeometryBlock) for child in item.children)


# --- JSON -------------------------------------------------------------------


def test_json_headings_follow_the_nesting():
    nodes = JsonParser().parse('{"a": {"b": "1"}}')
    headings = [(node.level, flatten(node)) for node in nodes if isinstance(node, Heading)]
    assert headings == [(1, "a"), (2, "b")]
    assert text_of([node for node in nodes if isinstance(node, Paragraph)]) == ["1"]


def test_json_list_of_links():
    nodes = JsonParser().parse('{"links": [{"url": "u", "title": "t"}]}')
    listing = [node for node in nodes if isinstance(node, List)][0]
    link = listing.children[0].children[0]
    assert isinstance(link, Link)
    assert (link.url, link.title) == ("u", "t")


def test_json_list_of_images_needs_alt():
    nodes = JsonParser().parse('{"images": [{"url": "u", "title": "t", "alt": "a"}]}')
    listing = [node for node in nodes if isinstance(node, List)][0]
    assert isinstance(listing.children[0].children[0], Image)


def test_json_invalid_document_is_reported():
    with pytest.raises(InvalidDocumentError, match="not valid JSON"):
        JsonParser().parse("{")


def test_json_top_level_must_be_an_object():
    with pytest.raises(InvalidDocumentError, match="must be an object"):
        JsonParser().parse("[1, 2]")


# --- GeoJSON ----------------------------------------------------------------


def _feature(title=None, name=None, geometry=POINT, **properties):
    feature = {"type": "Feature", "properties": dict(properties), "geometry": geometry}
    if title is not None:
        feature["title"] = title
    if name is not None:
        feature["properties"]["name"] = name
    return feature


def _collection(*features, title="Trip"):
    collection = {"type": "FeatureCollection", "features": list(features)}
    if title is not None:
        collection["title"] = title
    return json.dumps(collection)


def test_geojson_feature_titles_become_headings():
    nodes = GeoJsonParser().parse(_collection(_feature("Park Güell")))
    headings = [(node.level, flatten(node)) for node in nodes if isinstance(node, Heading)]
    assert headings[0] == (1, "Trip")
    assert (2, "Park Güell") in headings


def test_geojson_without_a_title_uses_properties_name():
    nodes = GeoJsonParser().parse(_collection(_feature(name="Main St"), title=None))
    assert isinstance(nodes[0], Heading)
    assert flatten(nodes[0]) == UNTITLED
    assert (2, "Main St") in [
        (node.level, flatten(node)) for node in nodes if isinstance(node, Heading)
    ]


def test_geojson_without_any_title_numbers_the_feature():
    nodes = GeoJsonParser().parse(_collection(_feature(title=None), title=None))
    assert (2, "Feature 1") in [
        (node.level, flatten(node)) for node in nodes if isinstance(node, Heading)
    ]


def test_duplicate_feature_titles_do_not_overwrite_each_other():
    """Two features with one heading used to leave a single feature behind."""
    document = _collection(_feature("Stop", n=1), _feature("Stop", n=2))
    nodes = GeoJsonParser().parse(document)
    titles = [flatten(node) for node in nodes if isinstance(node, Heading) and node.level == 2]
    assert titles == ["Stop", "Stop (2)"]
    assert text_of([node for node in nodes if isinstance(node, Paragraph)]) == ["1", "2"]


def test_a_bare_feature_is_read_as_one_feature():
    document = json.dumps(_feature("Only one"))
    nodes = GeoJsonParser().parse(document)
    assert len([node for node in nodes if isinstance(node, GeometryBlock)]) == 1


def test_a_bare_geometry_is_wrapped_in_a_feature():
    nodes = GeoJsonParser().parse(json.dumps(POINT))
    assert flatten(nodes[0]) == UNTITLED
    assert isinstance(nodes[1], Heading)
    assert flatten(nodes[1]) == "Feature 1"


def test_a_null_geometry_still_makes_a_feature():
    nodes = GeoJsonParser().parse(_collection(_feature("Nowhere", geometry=None)))
    blocks = [node for node in nodes if isinstance(node, GeometryBlock)]
    assert len(blocks) == 1
    assert blocks[0].geometry is None


def test_metadata_field_mapping_is_inverted_for_the_comment():
    feature = _feature("Park", overview="A park")
    feature["_metadata"] = {
        "field_mapping": {"overview": "Overview"},
        "extra_fields": ["title"],
    }
    nodes = GeoJsonParser().parse(_collection(feature))
    comment = [node for node in nodes if isinstance(node, HtmlBlock)][0].raw
    assert "- Overview: overview" in comment
    headings = [flatten(node) for node in nodes if isinstance(node, Heading)]
    assert "Overview" in headings


def test_extra_fields_that_exist_as_properties_keep_their_value():
    feature = _feature("Park", overview="A park")
    feature["properties"]["title"] = "Park"
    feature["_metadata"] = {"field_mapping": {}, "extra_fields": ["title"]}
    nodes = GeoJsonParser().parse(_collection(feature))
    comment = [node for node in nodes if isinstance(node, HtmlBlock)][0].raw
    assert "- title: Park" in comment


def test_extra_fields_are_not_repeated_as_sections():
    feature = _feature("Park", overview="A park")
    feature["_metadata"] = {"field_mapping": {}, "extra_fields": ["title"]}
    nodes = GeoJsonParser().parse(_collection(feature))
    headings = [flatten(node) for node in nodes if isinstance(node, Heading)]
    assert headings == ["Trip", "Park", "overview", "geometry"]


def test_unknown_top_level_type_is_rejected():
    with pytest.raises(InvalidDocumentError, match="expected a FeatureCollection"):
        GeoJsonParser().parse('{"type": "Nope"}')


def test_features_must_be_objects():
    with pytest.raises(InvalidDocumentError, match=r"features\[0\]"):
        GeoJsonParser().parse('{"type": "FeatureCollection", "features": [1]}')


def test_feature_type_is_checked():
    with pytest.raises(InvalidDocumentError, match="must be a Feature"):
        GeoJsonParser().parse(
            '{"type": "FeatureCollection", "features": [{"type": "Nope"}]}'
        )


def test_invalid_json_is_reported_with_a_position():
    with pytest.raises(InvalidDocumentError, match="line 1"):
        GeoJsonParser().parse('{"type": ')


def test_a_null_properties_member_is_read_as_empty():
    document = {
        "type": "FeatureCollection",
        "features": [{"type": "Feature", "properties": None, "geometry": POINT}],
    }
    nodes = GeoJsonParser().parse(json.dumps(document))
    assert isinstance(nodes[1], Heading)
