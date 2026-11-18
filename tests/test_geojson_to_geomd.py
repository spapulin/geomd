import geomd as gmd


def test_convert_returns_non_empty_string(geojson_feature_collection):
    result = gmd.convert(text=geojson_feature_collection, src="geojson", dst="geomd")
    assert isinstance(result, str) and result.strip()


def test_convert_returns_headings(geojson_feature_collection):
    result = gmd.convert(text=geojson_feature_collection, src="geojson", dst="geomd")
    for value in [
        "# Barcelona Tour",
        "## Park Güell",
        "## Casa Batlló"
    ]:
        assert value in result


def test_convert_returns_geometry_fenced_code_block(geojson_feature_collection):
    result = gmd.convert(text=geojson_feature_collection, src="geojson", dst="geomd")
    assert '```geometry\n{"type": "Point", "coordinates": [2.1527, 41.4145]}' in result
    assert '```geometry\n{"type": "Point", "coordinates": [2.16487, 41.391642]}' in result


def test_convert_add_auto_contents(geojson_feature_collection):
    result = gmd.convert(
        text=geojson_feature_collection,
        src="geojson",
        dst="geomd",
        auto_contents=True
    )

    for value in [
        "### Contents",
        "- [Park Güell](#Park-Güell)",
        "- [Casa Batlló](#Casa-Batlló)"
    ]:
        assert value in result
