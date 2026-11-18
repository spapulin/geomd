import pytest
import json
import geomd as gmd


def test_convert_returns_non_empty_string(geomd_feature_collection):
    result = gmd.convert(text=geomd_feature_collection, src="geomd", dst="geojson")
    assert isinstance(result, str) and result.strip()


def test_convert_returns_features(geomd_feature_collection):
    result = gmd.convert(text=geomd_feature_collection, src="geomd", dst="geojson")

    feature_collection = json.loads(result)

    assert "features" in feature_collection
    assert len(feature_collection["features"]) == 2

    assert feature_collection["features"][0]["type"] == "Feature"
    assert feature_collection["features"][0]["title"] == "Park Güell"
    assert feature_collection["features"][0]["properties"]["Overview"].startswith("Park Güell is a public park system")
    assert feature_collection["features"][0]["geometry"]["type"] == "Point"
    assert feature_collection["features"][0]["geometry"]["coordinates"] == pytest.approx([2.152777, 41.414444])

    assert feature_collection["features"][1]["type"] == "Feature"
    assert feature_collection["features"][1]["title"] == "Casa Batlló"
    assert feature_collection["features"][1]["properties"]["Overview"].startswith("Casa Batlló is a renowned building")
    assert feature_collection["features"][1]["geometry"]["type"] == "Point"
    assert feature_collection["features"][1]["geometry"]["coordinates"] == pytest.approx([2.16487, 41.391642])
