import logging

import geojson

from ..parsers.json_parser import JsonParser
from ..helpers import render_metadata_as_html_comment
from ..models import Node, Heading, Text, Paragraph, GeometryBlock, HtmlBlock
from ..constants import _METADATA_KEY, _EXTRA_FIELDS, _FIELD_MAPPING

logger = logging.getLogger(__name__)


class GeoJsonParser(JsonParser):
    """
    Parse GeoJSON text into a flat list of document nodes.
    """

    def parse(self, text: str) -> list[Node]:

        geojson_dict = geojson.loads(text)
        geojson_dict.pop("type", None)

        root_title = geojson_dict.pop("title", None) or ""
        features = geojson_dict.pop("features", [])

        content: dict = dict(geojson_dict)

        for feature in features:
            title = feature["title"] or ""
            entry = {}

            metadata = feature.get(_METADATA_KEY)
            if metadata:
                entry[_METADATA_KEY] = metadata

            entry.update(feature.get("properties") or {})
            entry["geometry"] = feature["geometry"]
            content[title] = entry

        return self._to_nodes({root_title: content})

    def _to_nodes(self, data: dict, level: int = 1) -> list[Node]:

        nodes: list[Node] = []

        metadata = data.get(_METADATA_KEY) or {}
        field_mapping = metadata.get(_FIELD_MAPPING) or {}
        extra_fields = {name: None for name in metadata.get(_EXTRA_FIELDS) or []}

        for key, value in data.items():
            if key == _METADATA_KEY:
                continue

            if key in extra_fields:
                extra_fields[key] = value
                continue

            nodes.append(Heading(
                level=level,
                children=[Text(raw=field_mapping.get(key, key))],
            ))

            if isinstance(value, dict):
                if key == "geometry":
                    nodes.append(GeometryBlock(geometry=value))
                else:
                    nodes.extend(self._to_nodes(value, level + 1))
            elif isinstance(value, list):
                nodes.append(self._to_list_node(value))
            else:
                nodes.append(Paragraph(children=[Text(raw=str(value))]))

        if metadata:
            nodes.insert(0, HtmlBlock(
                raw=render_metadata_as_html_comment({
                    _EXTRA_FIELDS: extra_fields,
                    _FIELD_MAPPING: {v: k for k, v in field_mapping.items()}
                })
            ))

        return nodes

