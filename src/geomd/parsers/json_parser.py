import json
import logging

from geomd.models import Node, Heading, Text, Paragraph, Image, Link, ListItem, List


logger = logging.getLogger(__name__)


class JsonParser:
    """Convert a JSON document into a flat list of document nodes."""

    def parse(self, text: str) -> list[Node]:
        data = json.loads(text)
        return self._to_nodes(data)

    def _to_nodes(self, data: dict, level: int = 1) -> list[Node]:
        nodes: list[Node] = []
        for key, value in data.items():

            nodes.append(Heading(level=level, children=[Text(raw=key)]))

            if isinstance(value, dict):
                nodes.extend(self._to_nodes(value, level + 1))

            elif isinstance(value, list):
                nodes.append(self._to_list_node(value))
            else:
                nodes.append(Paragraph(children=[Text(raw=str(value))]))

        return nodes

    def _to_list_node(self, items: list) -> Node:
        list_nodes: list[ListItem] = []
        for item in items:
            node = self._to_resource_node(item)
            if node is not None:
                list_nodes.append(ListItem(children=[node]))
        return List(children=list_nodes)

    def _to_resource_node(self, item: str | dict) -> Node | None:
        if not isinstance(item, dict):
            return Text(raw=str(item))

        url = item.get("url")
        title = item.get("title")

        if not url and not title:
            return None

        if "alt" in item:
            alt = item["alt"]
            return Image(url=url, title=title, alt=alt)

        return Link(url=url, title=title)

