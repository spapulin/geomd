from __future__ import annotations

import geojson

from ..errors import InvalidGeometryError
from ..models import GeometryBlock, Node
from .markdown_renderer import MarkdownRenderer, _fenced


class GeoMarkdownRenderer(MarkdownRenderer):
    """Render document nodes to GeoMarkdown text."""

    def _render_block(self, node: Node) -> str:
        if isinstance(node, GeometryBlock):
            return _fenced("geometry", self._geometry_body(node))
        return super()._render_block(node)

    @staticmethod
    def _geometry_body(node: GeometryBlock) -> str:
        if node.error:
            # Keep a block that could not be read exactly as it was written.
            return node.raw
        if node.geometry is None:
            return "null"
        try:
            return geojson.dumps(node.geometry)
        except (TypeError, ValueError) as exc:  # pragma: no cover - defensive
            raise InvalidGeometryError(f"cannot serialise the geometry ({exc})") from exc
