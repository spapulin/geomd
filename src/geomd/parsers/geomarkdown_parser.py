import logging
from json import JSONDecodeError

import geojson

from .markdown_parser import MarkdownParser
from .. import CodeBlock
from ..models import Node, GeometryBlock


logger = logging.getLogger(__name__)


_GEOMETRY_LANGUAGE = "geometry"


class GeoMarkdownParser(MarkdownParser):
    """
    Markdown parser that upgrades ```geometry blocks into GeometryBlock nodes.
    """

    def parse(self, text: str) -> list[Node]:
        nodes = super().parse(text)
        return self._apply_geometry_block(nodes)

    def _apply_geometry_block(self, nodes: list[Node]) -> list[Node]:
        for i, node in enumerate(nodes):
            if isinstance(node, CodeBlock) and node.language == _GEOMETRY_LANGUAGE:
                try:
                    geometry = geojson.loads(node.raw)
                except JSONDecodeError as e:
                    logger.warning("Failed to parse geometry block: %s; raw=%r", e, node.raw)
                    geometry = None
                # Replace CodeBlock with GeometryBlock
                nodes[i] = GeometryBlock(geometry=geometry)
        return nodes
