import geojson

from .markdown_renderer import MarkdownRenderer
from ..models import GeometryBlock


class GeoMarkdownRenderer(MarkdownRenderer):
    """Render document nodes back to Markdown text."""

    def _render_geometry_block(self, node: GeometryBlock) -> str:
        return f"```geometry\n{geojson.dumps(node.geometry)}\n```"

