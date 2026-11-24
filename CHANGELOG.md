# Changelog

## [0.2.0] - 2026-11-24

### Added

- Add auto-generated table of contents from `h2` headings (via `auto_contents`).
- Add `as_dict` argument to renderers to control output type (`str | dict`).
- Add `ImageList` node, rendered as an inline row in the HTML renderer.
- Add `geomd` as FastAPI and FastMCP services.

### Changed

- `GeoJsonRenderer` auto-detects the geometry field when not provided in metadata.
- `JsonRenderer` renders `CodeBlock` and `GeometryBlock` as dicts with `language` and `code` keys.
