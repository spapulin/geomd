from __future__ import annotations

import logging

import mistune

from geomd.models import (
    CodeBlock,
    Formatting,
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

_md = mistune.create_markdown(renderer=None)

#: Tokens with no dedicated node whose raw text is kept verbatim.  Dropping
#: them would silently shorten a paragraph.
_RAW_TOKENS = frozenset({"codespan", "inline_html"})

_FORMATTING_MARKUP = {"strong": "**", "emphasis": "*", "strikethrough": "~~"}


class MarkdownParser:
    """Convert a Markdown document into a flat list of document nodes."""

    def parse(self, text: str) -> list[Node]:
        ast, _ = _md.parse(text)
        nodes = []
        for token in ast:
            node = self._to_nodes(token)
            if node is not None:
                nodes.append(node)
        return nodes

    def _to_nodes(self, node: dict) -> Node | None:
        node_type = node["type"]
        attrs = node.get("attrs") or {}

        match node_type:
            case "heading":
                return Heading(level=attrs["level"], children=self._get_children(node))
            case "paragraph" | "block_text":
                return Paragraph(children=self._get_children(node))
            case "text":
                return Text(raw=node["raw"])
            case "strong" | "emphasis" | "strikethrough":
                return Formatting(
                    markup=_FORMATTING_MARKUP[node_type],
                    children=self._get_children(node),
                )
            case "softbreak":
                return Text(raw="\n")
            case "linebreak":
                return Text(raw="  \n")
            case "block_code":
                return CodeBlock(
                    language=attrs.get("info") or "",
                    raw=(node.get("raw") or "").rstrip("\n"),
                )
            case "link":
                return Link(url=attrs.get("url") or "", title=self._inline_text(node))
            case "image":
                return Image(
                    url=attrs.get("url") or "",
                    alt=self._inline_text(node),
                    title=attrs.get("title") or "",
                )
            case "list":
                return List(
                    ordered=bool(attrs.get("ordered", False)),
                    start=_list_start(attrs),
                    depth=int(attrs.get("depth", 0) or 0),
                    children=self._get_children(node),
                )
            case "list_item":
                return ListItem(children=self._get_children(node))
            case "block_html":
                return HtmlBlock(raw=(node.get("raw") or "").rstrip("\n"))
            case "thematic_break":
                return Paragraph(children=[Text(raw="---")])
            case "block_quote":
                # Keep the words; a quote has no node of its own.
                return Paragraph(children=self._get_children(node))
            case "blank_line":
                return None
            case _:
                raw = node.get("raw")
                if node_type in _RAW_TOKENS and raw is not None:
                    return Text(raw=raw)
                if raw:
                    logger.warning("No node for token %r, keeping its raw text", node_type)
                    return Text(raw=raw)
                logger.warning("Dropping unsupported token %r", node_type)
                return None

    def _get_children(self, node: dict) -> list[Node]:
        """Convert every child token, skipping the ones that carry no content.

        The conversion must not run inside the comprehension's filter: the
        filter is evaluated before the element expression, so it would test the
        *previous* child and drop everything after an unhandled token.
        """
        children: list[Node] = []
        for child in node.get("children") or []:
            converted = self._to_nodes(child)
            if converted is not None:
                children.append(converted)
        return children

    def _inline_text(self, node: dict) -> str:
        """Plain text of a token's descendants (link text, image alt text)."""
        parts: list[str] = []
        for child in node.get("children") or []:
            raw = child.get("raw")
            if raw:
                parts.append(raw)
            else:
                parts.append(self._inline_text(child))
        return "".join(parts)


def _list_start(attrs: dict) -> int:
    start = attrs.get("start")
    try:
        return int(start) if start is not None else 1
    except (TypeError, ValueError):
        return 1
