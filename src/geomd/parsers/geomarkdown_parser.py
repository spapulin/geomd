from __future__ import annotations

import logging

from ..errors import InvalidGeometryError
from ..geometry import loads_geometry
from ..models import CodeBlock, GeometryBlock, Node
from .markdown_parser import MarkdownParser

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
        for index, node in enumerate(nodes):
            if isinstance(node, CodeBlock) and node.language.strip() == _GEOMETRY_LANGUAGE:
                nodes[index] = _geometry_block(node.raw)
            elif node.children:
                node.children = self._apply_geometry_block(node.children)
        return nodes


def _geometry_block(raw: str) -> GeometryBlock:
    """Turn a ```geometry code block into a GeometryBlock.

    A block that cannot be read is kept verbatim (``raw`` plus ``error``) so
    that writing the document back cannot replace it with ``null``.
    """
    try:
        return GeometryBlock(geometry=loads_geometry(raw), raw=raw.strip())
    except InvalidGeometryError as exc:
        logger.warning("Keeping the text of a rejected geometry block: %s", exc.reason)
        return GeometryBlock(geometry=None, raw=raw.strip(), error=str(exc))
