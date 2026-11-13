import json
from pathlib import Path

import geomd

ASSETS = Path(__file__).resolve().parents[1] / "assets"


def test_the_repository_sample_survives_a_full_round_trip():
    geojson_text = (ASSETS / "barcelona_tour.geojson").read_text(encoding="utf-8")
    markdown = geomd.convert(geojson_text, "geojson", "geomd")
    back = geomd.convert(markdown, "geomd", "geojson", as_dict=True)

    original = json.loads(geojson_text)
    assert back["title"] == original["title"]
    assert len(back["features"]) == len(original["features"])
    for produced, expected in zip(back["features"], original["features"], strict=True):
        assert produced["title"] == expected["title"]
        assert produced["geometry"] == expected["geometry"]
        assert produced["properties"]["overview"] == expected["properties"]["overview"]
        assert produced["properties"]["address"] == expected["properties"]["address"]


def test_geomarkdown_output_is_stable():
    markdown = geomd.convert(
        (ASSETS / "barcelona_tour.geojson").read_text(encoding="utf-8"), "geojson", "geomd"
    )
    once = geomd.convert(markdown, "geomd", "geomd")
    twice = geomd.convert(once, "geomd", "geomd")
    assert once == twice


def test_the_sample_markdown_matches_the_sample_geojson():
    markdown = (ASSETS / "barcelona_tour.md").read_text(encoding="utf-8")
    produced = geomd.convert(markdown, "geomd", "geojson", as_dict=True)
    expected = json.loads((ASSETS / "barcelona_tour.geojson").read_text(encoding="utf-8"))
    assert produced["title"] == expected["title"]
    assert [feature["title"] for feature in produced["features"]] == [
        feature["title"] for feature in expected["features"]
    ]


def test_two_conversions_of_the_same_input_are_identical():
    markdown = (ASSETS / "barcelona_tour.md").read_text(encoding="utf-8")
    assert geomd.convert(markdown, "geomd", "geojson") == geomd.convert(
        markdown, "geomd", "geojson"
    )


def test_version_matches_the_packaging_metadata():
    pyproject = (Path(__file__).resolve().parents[1] / "pyproject.toml").read_text(encoding="utf-8")
    assert f'version = "{geomd.__version__}"' in pyproject
