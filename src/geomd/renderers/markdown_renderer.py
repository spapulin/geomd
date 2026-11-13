from __future__ import annotations

import logging

import geojson

from geomd.models import (
    CodeBlock,
    Formatting,
    GeometryBlock,
    Heading,
    HtmlBlock,
    Image,
    Link,
    List,
    ListItem,
    Node,
    Paragraph,
    Text,
)

logger = logging.getLogger(__name__)

LIST_INDENT = 2


class MarkdownRenderer:
    """Render document nodes back to Markdown text.

    This is the plain Markdown destination: a geometry block is written as a
    ``json`` fence so the output is valid Markdown without geomd's dialect.
    """

    def render(self, nodes: list[Node], **kwargs) -> str:
        return self._to_markdown(nodes)

    def _to_markdown(self, nodes: list[Node]) -> str:
        """Convert each block node to its Markdown form, joined by blank lines."""

        blocks: list[str] = []
        for node in nodes:
            rendered = self._render_block(node)
            if rendered:
                blocks.append(rendered)
        return "\n\n".join(blocks) + "\n" if blocks else ""

    def _render_block(self, node: Node) -> str:
        if isinstance(node, Heading):
            return "#" * node.level + " " + self._render_inline(node.children)
        if isinstance(node, Paragraph):
            return self._render_inline(node.children)
        if isinstance(node, List):
            return self._render_list(node)
        if isinstance(node, CodeBlock):
            return _fenced(node.language, node.raw)
        if isinstance(node, HtmlBlock):
            return node.raw
        if isinstance(node, GeometryBlock):
            return _fenced("json", _geometry_body(node))
        raise ValueError(f"No such block node: {node.NODE_TYPE}")

    def _render_list(self, node: List, indent: int = 0) -> str:
        """Render list items as Markdown bullets or numbered entries."""
        lines: list[str] = []
        pad = " " * max(indent, node.depth * LIST_INDENT)

        number = node.start if node.ordered else 1
        for item in node.children:
            marker = f"{number}. " if node.ordered else "- "
            number += 1
            body, nested = self._split_item(item)
            body_lines = body.splitlines() or [""]

            # First line carries the marker; continuation lines are indented
            # to line up with the item's text
            lines.append(pad + marker + body_lines[0])
            continuation = " " * len(marker)
            for line in body_lines[1:]:
                lines.append(pad + continuation + line)
            for child in nested:
                lines.append(self._render_list(child, indent=len(pad) + len(marker)))

        return "\n".join(lines)

    def _split_item(self, item: ListItem) -> tuple[str, list[List]]:
        """Separate an item's own text from lists nested under it."""
        inline: list[Node] = []
        nested: list[List] = []
        for child in item.children:
            if isinstance(child, List):
                nested.append(child)
            else:
                inline.append(child)
        body = self._render_inline(inline).strip()
        return body, nested

    def _render_inline(self, nodes: list[Node]) -> str:
        """Flatten inline nodes (Text/Link/Image/Formatting) to a single string."""

        result: list[str] = []
        for node in nodes:
            if isinstance(node, Text):
                result.append(node.raw)
            elif isinstance(node, Formatting):
                inner = self._render_inline(node.children)
                result.append(f"{node.markup}{inner}{node.markup}")
            elif isinstance(node, Link):
                result.append(f"[{node.title}]({node.url})")
            elif isinstance(node, Image):
                # Standard Markdown: ![alt](url "title")
                title = f' "{node.title}"' if node.title else ""
                result.append(f"![{node.alt}]({node.url}{title})")
            elif isinstance(node, Paragraph):
                result.append(self._render_inline(node.children))
            elif isinstance(node, List):
                result.append(self._render_list(node))
            elif node.children:
                result.append(self._render_inline(node.children))
            else:
                raise ValueError(f"No such inline node: {node.NODE_TYPE}")
        return "".join(result)


def _fenced(language: str, body: str) -> str:
    """Fence a block, using a longer fence than any backtick run inside it."""
    longest = 0
    for line in (body or "").splitlines():
        stripped = line.strip()
        if stripped and set(stripped) == {"`"}:
            longest = max(longest, len(stripped))
    fence = "`" * max(3, longest + 1)
    return f"{fence}{language}\n{body}\n{fence}"


def _geometry_body(node: GeometryBlock) -> str:
    if node.geometry is None:
        return node.raw or "null"
    return geojson.dumps(node.geometry)
