import geojson

from .markdown_renderer import MarkdownRenderer
from ..models import Node, Heading, Paragraph, List, CodeBlock, GeometryBlock, HtmlBlock


class GeoMarkdownRenderer(MarkdownRenderer):
    """Render document nodes back to Markdown text."""

    def render(self, nodes: list[Node]) -> str:
        return self._to_markdown(nodes)

    def _to_markdown(self, nodes: list[Node]) -> str:
        """Convert each block node to its Markdown form, joined by blank lines."""

        blocks: list[str] = []
        for node in nodes:
            if isinstance(node, Heading):
                blocks.append("#" * node.level + " " + self._render_inline(node.children))
            elif isinstance(node, Paragraph):
                blocks.append(self._render_inline(node.children))
            elif isinstance(node, List):
                blocks.append(self._render_list(node.children, ordered=node.ordered))
            elif isinstance(node, CodeBlock):
                language = node.language or ""
                blocks.append(f"```{language}\n{node.raw}\n```")
            elif isinstance(node, HtmlBlock):
                blocks.append(f"{node.raw}")
            elif isinstance(node, GeometryBlock):
                blocks.append(f"```geometry\n{geojson.dumps(node.geometry)}\n```")
            else:
                raise ValueError(f"No such block node: {node.NODE_TYPE}")
        return "\n\n".join(blocks) + "\n"