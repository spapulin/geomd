import logging

import mistune

from geomd.models import Node, Heading, Paragraph, Text, CodeBlock, Link, Image, List, ListItem, HtmlBlock

logger = logging.getLogger(__name__)

_md = mistune.create_markdown(renderer=None)


class MarkdownParser:
    """Convert a Markdown document into a flat list of document nodes."""

    def parse(self, text: str) -> list[Node]:
        ast, _ = _md.parse(text)
        nodes = []
        for node in ast:
            node = self._to_nodes(node)
            if node is not None:
                nodes.append(node)
        return nodes

    def _to_nodes(self, node: dict) -> Node | None:
        node_type = node["type"]
        match node_type:
            case "heading":
                return Heading(
                    level=node["attrs"]["level"],
                    children=self._get_children(node)
                )
            case "paragraph" | "block_text":
                return Paragraph(
                    children=self._get_children(node)
                )
            case "text":
                return Text(raw=node["raw"])
            case "block_code":
                return CodeBlock(
                    language=node.get("attrs", {}).get("info", ""),
                    raw=node["raw"]
                )
            case "link":
                title = ""
                children = node.get("children")
                if children:
                    title = children[0].get("raw")
                return Link(
                    url=node["attrs"]["url"],
                    title=title,
                )
            case "image":
                title = ""
                children = node.get("children")
                if children:
                    title = children[0].get("raw")
                return Image(
                    url=node["attrs"]["url"],
                    alt=node["attrs"].get("title") or "",
                    title=title
                )
            case "list":
                return List(
                    ordered=node["bullet"] != "-",
                    children=self._get_children(node)
                )
            case "list_item":
                return ListItem(
                    children=self._get_children(node)
                )
            case "block_html":
                return HtmlBlock(raw=node.get("raw"))
            case "blank_line":
                return None
            case _:
                raise ValueError(f"unhandled token: {node_type}")

    def _get_children(self, node: dict) -> list[Node]:
        return [
            node := self._to_nodes(child)
            for child in node.get("children") or []
            if node is not None
        ]
