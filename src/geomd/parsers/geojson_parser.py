from __future__ import annotations

import json
import logging

import geojson

from ..constants import _EXTRA_FIELDS, _FIELD_MAPPING, _METADATA_KEY
from ..errors import InvalidDocumentError
from ..geometry import GEOMETRY_TYPES, validate_geometry
from ..helpers import render_metadata_as_html_comment
from ..models import (
    GeometryBlock,
    Heading,
    HtmlBlock,
    List,
    ListItem,
    Node,
    Paragraph,
    Text,
)
from .json_parser import JsonParser

logger = logging.getLogger(__name__)

#: Heading used when a FeatureCollection carries no title of its own.
UNTITLED = "Untitled"


class GeoJsonParser(JsonParser):
    """Parse GeoJSON text into a flat list of document nodes.

    Accepts a ``FeatureCollection``, a bare ``Feature`` or a bare geometry.
    Only the ``title`` and ``_metadata`` foreign members are required to be
    geomd's own; every other GeoJSON document is read as well, with the
    feature heading taken from ``title``, ``properties.title``,
    ``properties.name`` or ``Feature <n>`` in that order.
    """

    def parse(self, text: str) -> list[Node]:
        data = self._load(text)
        title, features = self._split(data)

        nodes: list[Node] = [
            Heading(level=1, children=[Text(raw=title)])
        ]
        used_titles: dict[str, int] = {}
        for index, feature in enumerate(features, start=1):
            nodes.extend(self._feature_nodes(feature, index, used_titles))
        return nodes

    def _load(self, text: str) -> dict:
        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            raise InvalidDocumentError(
                f"the input is not valid JSON ({exc.msg} at line {exc.lineno}, column {exc.colno})"
            ) from exc
        if not isinstance(data, dict):
            raise InvalidDocumentError(
                f"a GeoJSON document must be a JSON object, got {type(data).__name__}"
            )
        return data

    def _split(self, data: dict) -> tuple[str, list[dict]]:
        """Return the collection title and the list of features."""
        kind = data.get("type")

        if kind == "FeatureCollection":
            features = data.get("features")
            if not isinstance(features, list):
                raise InvalidDocumentError("a FeatureCollection needs a 'features' list")
            title = data.get("title") or data.get("name") or ""
            return str(title) or UNTITLED, [self._as_feature(item, i) for i, item in enumerate(features, 1)]

        if kind == "Feature":
            title = data.get("title") or ""
            return str(title) or UNTITLED, [self._as_feature(data, 1)]

        if kind in GEOMETRY_TYPES:
            return UNTITLED, [self._as_feature({"type": "Feature", "geometry": data, "properties": {}}, 1)]

        raise InvalidDocumentError(
            f"expected a FeatureCollection, a Feature or a geometry, got {kind!r}"
        )

    def _as_feature(self, item: object, index: int) -> dict:
        """Normalise one entry of ``features`` into a Feature dict."""
        if not isinstance(item, dict):
            raise InvalidDocumentError(
                f"features[{index - 1}] must be a JSON object, got {type(item).__name__}"
            )
        kind = item.get("type")
        if kind in GEOMETRY_TYPES:
            return {"type": "Feature", "geometry": item, "properties": {}}
        if kind != "Feature":
            raise InvalidDocumentError(
                f"features[{index - 1}] must be a Feature, got type {kind!r}"
            )
        properties = item.get("properties")
        if properties is None:
            item = {**item, "properties": {}}
        elif not isinstance(properties, dict):
            raise InvalidDocumentError(
                f"features[{index - 1}] has a properties member that is not an object"
            )
        geometry = item.get("geometry")
        if geometry is not None:
            validate_geometry(geometry)
        return item

    def _feature_nodes(self, feature: dict, index: int, used_titles: dict[str, int]) -> list[Node]:
        properties: dict = feature.get("properties") or {}

        title = self._feature_title(feature, properties, index)
        title = _unique_title(title, used_titles)

        metadata = feature.get(_METADATA_KEY) or {}
        if not isinstance(metadata, dict):
            raise InvalidDocumentError(
                f"features[{index - 1}] has a {_METADATA_KEY} member that is not an object"
            )
        field_mapping = metadata.get(_FIELD_MAPPING) or {}
        if not isinstance(field_mapping, dict):
            raise InvalidDocumentError(
                f"features[{index - 1}] has a {_FIELD_MAPPING} that is not an object"
            )
        extras = metadata.get(_EXTRA_FIELDS) or []
        if not isinstance(extras, (list, tuple, dict)):
            raise InvalidDocumentError(
                f"features[{index - 1}] has an {_EXTRA_FIELDS} that is not a list of names"
            )
        extra_names = list(extras)

        nodes: list[Node] = [Heading(level=2, children=[Text(raw=title)])]

        if metadata:
            nodes.append(HtmlBlock(raw=render_metadata_as_html_comment({
                # Only names that exist as properties can carry a value.
                _EXTRA_FIELDS: {
                    name: properties[name] for name in extra_names if name in properties
                },
                _FIELD_MAPPING: {heading: key for key, heading in field_mapping.items()},
            })))

        for key, value in properties.items():
            if key in extra_names:
                continue
            nodes.append(Heading(level=3, children=[Text(raw=str(field_mapping.get(key, key)))]))
            nodes.extend(self._value_nodes(value))

        if "geometry" in feature:
            heading = field_mapping.get("geometry", "geometry")
            nodes.append(Heading(level=3, children=[Text(raw=str(heading))]))
            nodes.append(_geometry_node(feature["geometry"]))

        return nodes

    @staticmethod
    def _feature_title(feature: dict, properties: dict, index: int) -> str:
        for candidate in (
            feature.get("title"),
            properties.get("title"),
            properties.get("name"),
        ):
            if candidate:
                return str(candidate)
        return f"Feature {index}"

    def _value_nodes(self, value: object, level: int = 4) -> list[Node]:
        if isinstance(value, dict):
            nodes: list[Node] = []
            for key, nested in value.items():
                nodes.append(Heading(level=level, children=[Text(raw=str(key))]))
                nodes.extend(self._value_nodes(nested, level + 1))
            return nodes
        if isinstance(value, list):
            return [self._to_list_node(value)]
        return [Paragraph(children=[Text(raw="" if value is None else str(value))])]

    def _to_list_node(self, items: list) -> Node:
        list_nodes: list[ListItem] = []
        for item in items:
            node = self._to_resource_node(item)
            if node is not None:
                list_nodes.append(ListItem(children=[node]))
        return List(children=list_nodes)


def _unique_title(title: str, used: dict[str, int]) -> str:
    """Keep two features with the same heading apart instead of overwriting one."""
    count = used.get(title, 0) + 1
    used[title] = count
    if count == 1:
        return title
    logger.warning(
        "Two features are titled %r; the second becomes %r so neither is lost", title, f"{title} ({count})"
    )
    return f"{title} ({count})"


def _geometry_node(geometry: object) -> GeometryBlock:
    if geometry is None:
        return GeometryBlock(geometry=None, raw="null")
    if isinstance(geometry, dict):
        validate_geometry(geometry)
        return GeometryBlock(geometry=geojson.loads(json.dumps(geometry)))
    return GeometryBlock(geometry=geometry)
