import logging

import mistune

from ..models import Node, Heading, Paragraph, Text, CodeBlock, Link, Image, List, ListItem, HtmlBlock, TextBlock, \
    InlineFormat, ImageList, MetadataBlock
from ..constants import _EXTRA_FIELDS, _FIELD_MAPPING


logger = logging.getLogger(__name__)


class MarkdownParser:
    """Convert a Markdown document into a flat list of document nodes."""

    def __init__(self):
        self._md = mistune.create_markdown(renderer=None)

    def parse(self, text: str) -> list[Node]:
        ast, _ = self._md.parse(text)
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
            case "paragraph":
                return Paragraph(
                    children=self._get_children(node)
                )
            case "block_text":
                return TextBlock(
                    children=self._get_children(node)
                )
            case "text":
                return Text(raw=node["raw"])
            case "strong":
                return InlineFormat(
                    kind="**",
                    children=self._get_children(node)
                )
            case "emphasis":
                return InlineFormat(
                    kind="*",
                    children=self._get_children(node)
                )
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
                if self._is_image_list(node):
                    return ImageList(
                        children=self._get_children(node)
                    )
                else:
                    return List(
                        ordered=node["bullet"] != "-",
                        children=self._get_children(node)
                    )
            case "list_item":
                return ListItem(
                    children=self._get_children(node)
                )
            case "block_html":
                if not self._is_metadata_block(node):
                    return HtmlBlock(raw=node.get("raw"))
                else:
                    return MetadataBlock(raw=node.get("raw"))
            case "blank_line":
                return None
            case _:
                # raise ValueError(f"unhandled token: {node_type}")
                logger.error(f"Unhandled token: {node_type}")
                return None

    def _is_image_list(self, token):
        items = token.get("children", [])
        if not items:
            return False

        for item in items:
            if item.get("type") != "list_item":
                return False
            blocks = item.get("children", []) or []
            if not blocks:
                return False
            for block in blocks:
                if block.get("type") != "block_text":
                    return False

                if (not block.get("children", [])
                        or len(block["children"]) != 1
                        or block["children"][0].get("type") != "image"
                ):
                    return False

        return True

    def _is_metadata_block(self, token):
        text = token.get("raw")
        cleaned: str = text.strip()
        if not cleaned:
            return False

        if not (cleaned.startswith("<!--") and cleaned.endswith("-->")):
            return False

        body = cleaned[4:-3]

        has_metadata_keys = False
        has_properties = False

        field_names = {f"{_FIELD_MAPPING}:", f"{_EXTRA_FIELDS}:"}

        for raw_line in body.splitlines():
            line = raw_line.strip()
            if not line:
                continue

            if line in field_names:
                has_metadata_keys = True
                # Reset so each header must have properties
                has_properties = False
                continue

            # Reject properties before a header
            if not has_metadata_keys:
                return False

            if not line.startswith("- ") or not ":" in line:
                return False

            has_properties = True

        return has_metadata_keys and has_properties

    def _get_children(self, node: dict) -> list[Node]:
        children = []
        for child in node.get("children") or []:
            node = self._to_nodes(child)
            if node is not None:
                children.append(node)
        return children
