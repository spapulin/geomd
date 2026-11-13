import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from geomd.cli import default_destination, guess_format, main

ROOT = Path(__file__).resolve().parents[1]

GOOD = """# Trip

## Park

### Overview

Nice

### On map

```geometry
{"type": "Point", "coordinates": [1, 2]}
```
"""

COLLECTION = json.dumps({
    "type": "FeatureCollection",
    "title": "Trip",
    "features": [
        {
            "type": "Feature",
            "title": "Park",
            "geometry": {"type": "Point", "coordinates": [1, 2]},
            "properties": {"overview": "Nice"},
        }
    ],
})


def write(tmp_path, name, text):
    path = tmp_path / name
    path.write_text(text, encoding="utf-8")
    return path


def test_guess_format_from_the_file_name():
    assert guess_format("", "a.md") == "geomd"
    assert guess_format("", "a.markdown") == "geomd"
    assert guess_format('{"type": "FeatureCollection", "features": []}', "a.geojson") == "geojson"
    assert guess_format('{"a": 1}', "a.json") == "json"


def test_guess_format_from_the_content():
    assert guess_format(COLLECTION, "-") == "geojson"
    assert guess_format('{"a": 1}', "-") == "json"
    assert guess_format(GOOD, "-") == "geomd"


def test_default_destination_is_the_other_direction():
    assert default_destination("geojson") == "geomd"
    assert default_destination("geomd") == "geojson"


def test_convert_writes_json_to_stdout(tmp_path, capsys):
    path = write(tmp_path, "trip.md", GOOD)
    assert main(["convert", str(path)]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["features"][0]["geometry"] == {"type": "Point", "coordinates": [1, 2]}


def test_convert_guesses_the_geojson_side(tmp_path, capsys):
    path = write(tmp_path, "trip.geojson", COLLECTION)
    assert main(["convert", str(path)]) == 0
    assert capsys.readouterr().out.startswith("# Trip")


def test_convert_from_stdin(monkeypatch, capsys):
    monkeypatch.setattr("sys.stdin", __import__("io").StringIO(GOOD))
    assert main(["convert", "-", "--to", "geojson"]) == 0
    assert json.loads(capsys.readouterr().out)["title"] == "Trip"


def test_convert_writes_a_file(tmp_path):
    source = write(tmp_path, "trip.md", GOOD)
    target = tmp_path / "out.geojson"
    assert main(["convert", str(source), "-o", str(target)]) == 0
    assert json.loads(target.read_text(encoding="utf-8"))["type"] == "FeatureCollection"


def test_convert_compact_has_one_line(tmp_path, capsys):
    source = write(tmp_path, "trip.md", GOOD)
    assert main(["convert", str(source), "--compact"]) == 0
    assert len(capsys.readouterr().out.strip().splitlines()) == 1


def test_convert_indent_is_respected(tmp_path, capsys):
    source = write(tmp_path, "trip.md", GOOD)
    assert main(["convert", str(source), "--indent", "4"]) == 0
    assert '\n    "title"' in capsys.readouterr().out


def test_convert_to_markdown(tmp_path, capsys):
    source = write(tmp_path, "trip.geojson", COLLECTION)
    assert main(["convert", str(source), "--to", "md"]) == 0
    assert "```json" in capsys.readouterr().out


def test_convert_refuses_a_broken_geometry(tmp_path, capsys):
    source = write(tmp_path, "bad.md", GOOD.replace('"coordinates": [1, 2]', '"coordinates":'))
    assert main(["convert", str(source)]) == 1
    assert "refusing to convert" in capsys.readouterr().err


def test_convert_force_keeps_the_feature_with_a_null_geometry(tmp_path, capsys):
    source = write(tmp_path, "bad.md", GOOD.replace('"coordinates": [1, 2]', '"coordinates":'))
    assert main(["convert", str(source), "--force"]) == 0
    features = json.loads(capsys.readouterr().out)["features"]
    assert len(features) == 1
    assert features[0]["geometry"] is None


def test_convert_rejects_an_unknown_format(tmp_path, capsys):
    source = write(tmp_path, "trip.md", GOOD)
    with pytest.raises(SystemExit):
        main(["convert", str(source), "--to", "pdf"])


def test_convert_reports_an_empty_file(tmp_path, capsys):
    source = write(tmp_path, "empty.md", "  \n")
    assert main(["convert", str(source)]) == 2
    assert "empty" in capsys.readouterr().err


def test_convert_reports_a_missing_file(tmp_path, capsys):
    assert main(["convert", str(tmp_path / "nope.md")]) == 2
    assert "No such file" in capsys.readouterr().err


def test_check_is_quiet_for_a_good_document(tmp_path, capsys):
    source = write(tmp_path, "trip.md", GOOD)
    assert main(["check", str(source)]) == 0
    assert "no problems found" in capsys.readouterr().out


def test_check_fails_on_an_error(tmp_path, capsys):
    source = write(tmp_path, "bad.md", GOOD.replace('"coordinates": [1, 2]', '"coordinates":'))
    assert main(["check", str(source)]) == 1
    out = capsys.readouterr().out
    assert "error: line 11" in out


def test_check_json_output(tmp_path, capsys):
    source = write(tmp_path, "bad.md", GOOD.replace('"coordinates": [1, 2]', '"coordinates":'))
    assert main(["check", str(source), "--json"]) == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload[0]["level"] == "error"
    assert payload[0]["line"] == 11


def test_check_explicit_format(tmp_path, capsys):
    source = write(tmp_path, "data.txt", COLLECTION)
    assert main(["check", str(source), "--from", "geojson"]) == 0


def test_formats_command(capsys):
    assert main(["formats"]) == 0
    out = capsys.readouterr().out
    assert "geomd" in out and "html" in out


def test_version(capsys):
    with pytest.raises(SystemExit) as exitinfo:
        main(["--version"])
    assert exitinfo.value.code == 0
    assert "geomd" in capsys.readouterr().out


def _run(args, stdin=None):
    env = dict(os.environ)
    env["PYTHONPATH"] = str(ROOT / "src") + os.pathsep + env.get("PYTHONPATH", "")
    return subprocess.run(
        [sys.executable, "-m", "geomd", *args],
        cwd=ROOT,
        env=env,
        input=stdin,
        capture_output=True,
        text=True,
    )


def test_module_entry_point_converts():
    result = _run(["convert", "-", "--to", "geojson"], stdin=GOOD)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["title"] == "Trip"


def test_module_entry_point_exit_code_for_a_broken_document(tmp_path):
    path = write(tmp_path, "bad.md", GOOD.replace('"coordinates": [1, 2]', '"coordinates":'))
    result = _run(["check", str(path)])
    assert result.returncode == 1
    assert "error" in result.stdout
