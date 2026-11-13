import json

from geomd.validation import check_text, find_geometry_blocks

GOOD = '# Trip\n\n## Park\n\n### On map\n\n```geometry\n{"type": "Point", "coordinates": [1, 2]}\n```\n'


def levels(issues):
    return [issue.level for issue in issues]


def test_a_good_document_has_no_issues():
    assert check_text(GOOD, "geomd") == []


def test_geometry_blocks_carry_their_line():
    fences = find_geometry_blocks(GOOD)
    assert len(fences) == 1
    assert fences[0].line == 7
    assert fences[0].closed is True
    assert fences[0].body == '{"type": "Point", "coordinates": [1, 2]}'


def test_an_unclosed_fence_is_an_error():
    text = '# T\n\n## F\n\n```geometry\n{"type": "Point", "coordinates": [1, 2]}\n'
    fences = find_geometry_blocks(text)
    assert fences[0].closed is False
    issues = check_text(text, "geomd")
    assert any("never closed" in issue.message for issue in issues)
    assert "error" in levels(issues)


def test_an_invalid_geometry_names_the_reason_and_line():
    text = '# T\n\n## F\n\n```geometry\n{"type": "Point"}\n```\n'
    issues = check_text(text, "geomd")
    errors = [issue for issue in issues if issue.is_error]
    assert len(errors) == 1
    assert errors[0].line == 5
    assert "coordinates" in errors[0].message


def test_an_empty_geometry_block_is_an_error():
    text = '# T\n\n## F\n\n```geometry\n\n```\n'
    assert any("empty" in issue.message for issue in check_text(text, "geomd"))


def test_duplicate_feature_titles_get_a_line():
    text = '# T\n\n## F\n\n```geometry\nnull\n```\n\n## F\n\n```geometry\nnull\n```\n'
    issues = check_text(text, "geomd")
    duplicate = [issue for issue in issues if "two features" in issue.message]
    assert duplicate[0].line == 9
    assert "first on line 3" in duplicate[0].message


def test_a_geometry_under_the_top_heading_is_a_warning():
    text = '# T\n\n```geometry\nnull\n```\n'
    issues = check_text(text, "geomd")
    assert [issue.level for issue in issues] == ["warning"]
    assert "not inside a level-2 feature section" in issues[0].message


def test_a_geometry_before_any_heading_is_an_error():
    text = '```geometry\nnull\n```\n\n# T\n'
    issues = check_text(text, "geomd")
    assert any("before any heading" in issue.message for issue in issues)


def test_plain_markdown_without_geometry_is_clean():
    assert check_text("# T\n\n## A\n\ntext\n", "md") == []


def test_geojson_without_features_is_a_warning():
    issues = check_text('{"type": "FeatureCollection", "features": []}', "geojson")
    assert [issue.level for issue in issues] == ["warning"]


def test_geojson_broken_json_reports_the_line():
    issues = check_text('{\n  "type": ', "geojson")
    assert issues[0].is_error
    assert issues[0].line is not None


def test_geojson_feature_list_type_is_checked():
    issues = check_text('{"type": "FeatureCollection", "features": {}}', "geojson")
    assert issues[0].is_error


def test_geojson_features_must_be_objects():
    issues = check_text('{"type": "FeatureCollection", "features": ["x"]}', "geojson")
    assert any("features[0]" in issue.message for issue in issues)


def test_geojson_unexpected_type_is_an_error():
    issues = check_text('{"type": "Banana"}', "geojson")
    assert issues[0].is_error


def test_a_null_geometry_feature_is_not_reported():
    document = {
        "type": "FeatureCollection",
        "features": [{"type": "Feature", "properties": {}, "geometry": None}],
    }
    assert check_text(json.dumps(document), "geojson") == []


def test_unknown_formats_are_not_checked():
    assert check_text("whatever", "json") == []


def test_issue_str_includes_the_line():
    text = '# T\n\n## F\n\n```geometry\n{"type": "Point"}\n```\n'
    issue = check_text(text, "geomd")[0]
    assert str(issue).startswith("error: line 5: ")
