from __future__ import annotations

import json
import logging

from geomd.errors import InvalidDocumentError
from geomd.models import Heading, Image, Link, List, ListItem, Node, Paragraph, Text

logger = logging.getLogger(__name__)


class JsonParser:
    """Convert a JSON document into a flat list of document nodes."""

    def parse(self, text: str) -> list[Node]:
        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            raise InvalidDocumentError(
                f"the input is not valid JSON ({exc.msg} at line {exc.lineno}, column {exc.colno})"
            ) from exc
        if not isinstance(data, dict):
            raise InvalidDocumentError(
                f"the top level of a JSON document must be an object, got {type(data).__name__}"
            )
        return self._to_nodes(data)

    def _to_nodes(self, data: dict, level: int = 1) -> list[Node]:
        nodes: list[Node] = []
        for key, value in data.items():

            nodes.append(Heading(level=level, children=[Text(raw=str(key))]))

            if isinstance(value, dict):
                nodes.extend(self._to_nodes(value, level + 1))

            elif isinstance(value, list):
                nodes.append(self._to_list_node(value))
            else:
                nodes.append(Paragraph(children=[Text(raw="" if value is None else str(value))]))

        return nodes

    def _to_list_node(self, items: list) -> Node:
        list_nodes: list[ListItem] = []
        for item in items:
            node = self._to_resource_node(item)
            if node is not None:
                list_nodes.append(ListItem(children=[node]))
        return List(children=list(list_nodes))

    def _to_resource_node(self, item: str | dict) -> Node | None:
        if not isinstance(item, dict):
            return Text(raw=str(item))

        url = item.get("url")
        title = item.get("title")

        if not url and not title:
            return None

        if "alt" in item:
            alt = item["alt"]
            return Image(url=url or "", title=title or "", alt=str(alt or ""))

        return Link(url=url or "", title=title or "")
