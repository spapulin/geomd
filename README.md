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

## Try it online

The quickest way to see `geomd` in action is the hosted demo:

**[https://geomd.onrender.com/?url=https://raw.githubusercontent.com/spapulin/geomd/refs/heads/main/assets/barcelona_tour.geojson&src=geojson&dst=html](https://geomd.onrender.com/?url=https://raw.githubusercontent.com/spapulin/geomd/refs/heads/main/assets/barcelona_tour.geojson&src=geojson&dst=html)**

The service takes a GeoJSON file, reads it, and renders it back as HTML. The example above uses [`barcelona_tour.geojson`](https://raw.githubusercontent.com/spapulin/geomd/refs/heads/main/assets/barcelona_tour.geojson)

The service accepts three query parameters:

| Parameter | Description | Example |
|-----------|-------------|---------|
| `url` | Public URL of the source file | `https://raw.githubusercontent.com/.../barcelona_tour.geojson` |
| `src` | Source format | `geojson` |
| `dst` | Target format | `html` |

The demo server also exposes an interactive **Swagger UI** where you can explore and test the available endpoints directly from your browser:

**[https://geomd.onrender.com/docs](https://geomd.onrender.com/docs)**

## Command line

The package installs a `geomd` command (and `python -m geomd` does the same):

    geomd convert barcelona_tour.geojson --to geomd > tour.md
    geomd convert tour.md --to geojson -o tour.geojson
    geomd check tour.md

`convert` reads a file or `-` for standard input, guesses the source format
from the extension or the content, and writes to standard output unless `-o`
names a file. JSON and GeoJSON output is indented (`--indent N`, or
`--compact` for one line).

`check` reports what would not survive a conversion, with line numbers:

    $ geomd check broken.md
    error: line 7: Point needs a 'coordinates' member
    warning: line 11: two features are titled 'F' (first on line 3)

It exits non-zero when there is an error, so it works as a pre-commit step.
`convert` refuses a document that has errors rather than writing a GeoJSON
file that quietly lost a feature; `--force` converts anyway, keeping the
section and writing its geometry as `null`.

## What becomes a Feature

A document is read with the headings the specification describes:

- the top-level heading names the collection (`FeatureCollection.title`); a
  collection without a title gets the heading `Untitled`;
- a level-2 section becomes a `Feature` when its own content or the content of
  one of its direct subsections holds a `geometry` block. The `field_mapping`
  entry that renames a subsection to `geometry` is optional, as the
  specification says;
- a level-3 subsection becomes a property, and `field_mapping` renames it;
- a section without a geometry block is not a feature. Its content cannot be
  represented in GeoJSON, so it is reported through the `geomd` logger and left
  out of the output.

Features are collected from the heading tree, so two features with the same
heading both survive; the second one keeps its content and is titled
`Stop (2)`.

## Errors

Everything that cannot be converted raises `geomd.GeoMdError`, a `ValueError`:

| Error | Raised when |
|---|---|
| `UnknownFormatError` | the source or destination format is not registered |
| `InvalidDocumentError` | the text is not valid JSON, or not a FeatureCollection / Feature / geometry |
| `InvalidGeometryError` | a `geometry` block is not a GeoJSON geometry; it carries the reason and, from the CLI, the line |

A rejected geometry block is kept verbatim in the parsed document (`GeometryBlock.raw`
and `.error`), so `geomd` to `geomd` cannot turn a typo into `null`.

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