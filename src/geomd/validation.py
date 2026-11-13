"""Structural checks used by ``geomd check``.

The point is to find the documents that would convert into something
plausible but wrong, before they are converted: a geometry block that is not
inside a feature section, two features sharing a heading, a fence that never
closes, a geometry that is not a GeoJSON geometry.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass

from .errors import GeoMdError, InvalidGeometryError
from .geometry import GEOMETRY_TYPES, loads_geometry
from .parsers.geojson_parser import GeoJsonParser
from .parsers.geomarkdown_parser import GeoMarkdownParser

_HEADING = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")


@dataclass(frozen=True)
class Issue:
    level: str  # "error" or "warning"
    message: str
    line: int | None = None

    @property
    def is_error(self) -> bool:
        return self.level == "error"

    def __str__(self) -> str:
        where = f"line {self.line}: " if self.line is not None else ""
        return f"{self.level}: {where}{self.message}"


@dataclass(frozen=True)
class GeometryFence:
    line: int
    body: str
    closed: bool


def find_geometry_blocks(text: str) -> list[GeometryFence]:
    """Return every ```geometry fenced block, with the line its fence opens on."""
    blocks: list[GeometryFence] = []
    body: list[str] | None = None
    start_line = 0

    for number, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if body is None:
            if stripped.startswith("```") and stripped[3:].strip() == "geometry":
                body = []
                start_line = number
            continue
        if stripped.startswith("```") and stripped[3:].strip() == "":
            blocks.append(GeometryFence(start_line, "\n".join(body), True))
            body = None
            continue
        body.append(line)

    if body is not None:
        blocks.append(GeometryFence(start_line, "\n".join(body), False))
    return blocks


def check_text(text: str, fmt: str) -> list[Issue]:
    """Check a document of the given format and return everything wrong with it."""
    if fmt in ("md", "geomd"):
        return _check_markdown(text)
    if fmt == "geojson":
        return _check_geojson(text)
    return []


def _headings(text: str) -> list[tuple[int, int, str]]:
    headings = []
    for number, line in enumerate(text.splitlines(), start=1):
        match = _HEADING.match(line)
        if match:
            headings.append((number, len(match.group(1)), match.group(2)))
    return headings


def _check_markdown(text: str) -> list[Issue]:
    issues: list[Issue] = []
    headings = _headings(text)
    fences = find_geometry_blocks(text)

    for fence in fences:
        if not fence.closed:
            issues.append(Issue("error", "geometry block is never closed", fence.line))
        if fence.body.strip() == "":
            issues.append(Issue("error", "geometry block is empty", fence.line))
            continue
        try:
            loads_geometry(fence.body)
        except InvalidGeometryError as exc:
            issues.append(Issue("error", exc.reason, fence.line))

    seen: dict[str, int] = {}
    for line, level, title in headings:
        if level != 2:
            continue
        if title in seen:
            issues.append(Issue(
                "warning",
                f"two features are titled {title!r} (first on line {seen[title]})",
                line,
            ))
        else:
            seen[title] = line

    section_of = _section_lookup(headings)
    for fence in fences:
        level, title, line = section_of(fence.line)
        if level is None:
            issues.append(Issue(
                "error", "geometry block appears before any heading", fence.line
            ))
        elif level != 2:
            issues.append(Issue(
                "warning",
                f"geometry block sits under {title!r} (a level-{level} heading, line {line}), "
                "not inside a level-2 feature section",
                fence.line,
            ))

    try:
        GeoMarkdownParser().parse(text)
    except GeoMdError as exc:
        issues.append(Issue("error", str(exc)))

    return issues


def _section_lookup(headings: list[tuple[int, int, str]]):
    """Return a function giving the nearest feature (level-2) heading above a line.

    A geometry block may sit under any number of level-3+ subsections: those
    become the feature's properties, and the block becomes its geometry.
    """

    def lookup(line: int) -> tuple[int | None, str, int]:
        found: tuple[int | None, str, int] = (None, "", 0)
        for number, level, title in headings:
            if number >= line:
                break
            if level <= 2:
                found = (level, title, number)
        return found

    return lookup


def _check_geojson(text: str) -> list[Issue]:
    issues: list[Issue] = []
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        return [Issue("error", f"not valid JSON ({exc.msg})", exc.lineno)]

    if not isinstance(data, dict):
        return [Issue("error", "a GeoJSON document must be a JSON object")]

    kind = data.get("type")
    if kind == "FeatureCollection":
        features = data.get("features")
        if not isinstance(features, list):
            return [Issue("error", "FeatureCollection without a 'features' list")]
        if not features:
            issues.append(Issue("warning", "the FeatureCollection has no features"))
        for index, feature in enumerate(features):
            if not isinstance(feature, dict):
                issues.append(Issue("error", f"features[{index}] is not an object"))
    elif kind != "Feature" and kind not in GEOMETRY_TYPES:
        issues.append(Issue("error", f"unexpected top-level type {kind!r}"))

    try:
        GeoJsonParser().parse(text)
    except GeoMdError as exc:
        issues.append(Issue("error", str(exc)))

    return issues
