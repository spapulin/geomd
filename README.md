# geomd

[![Spec](https://img.shields.io/badge/spec-v0.1.0-blue)](SPEC.md)

GeoMarkdown is a Markdown dialect for geodata. This package provides parsers and renderers that convert between GeoMarkdown and GeoJSON

See the **[Specification](SPEC.md)** for the full notation.

## Quickstart

Walk through parsing and rendering in
[`notebooks/quickstart.ipynb`](notebooks/quickstart.ipynb).

Or, in three lines:

````python
import geomd as gmd

markdown_str = """
# Barcelona Tour

## Park Güell

<!--
field_mapping:
    - On map: geometry
-->

### Overview

A colorful park designed by Antoni Gaudí

### Address

Carrer d'Olot, Barcelona, Spain

### On map

```geometry
{"type": "Point", "coordinates": [2.1527, 41.4145]}
```
"""

# Convert from GeoMarkdown to GeoJSON
geojson_str = gmd.convert(
    text=markdown_str,
    src="geomd",
    dst="geojson"
)
print(geojson_str)
````

## Install

### As a library

With uv (recommended):

    uv add geomd

With pip:

    pip install geomd

### Development version

The latest unreleased code from `main`. May contain bugs, may
break without notice. Use only if you need a fix that hasn't
shipped to PyPI yet.

    uv add "geomd @ git+https://github.com/spapulin/geomd.git"
    pip install "geomd @ git+https://github.com/spapulin/geomd.git"

For reproducible installs, pin to a tag or commit:

    uv add "geomd @ git+https://github.com/spapulin/geomd.git@v0.1.0"

## Specification

GeoMarkdown is defined by **[Specification](SPEC.md)**. The spec is versioned independently of the package:

- Package: `geomd` is the Python implementation.
- Spec: `0.1.0` is the notation.

## License

[MIT](LICENSE)