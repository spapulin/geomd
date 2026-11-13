from __future__ import annotations

import json
import logging

from ..constants import _EXTRA_FIELDS, _FIELD_MAPPING, _METADATA_KEY
from ..geometry import GEOMETRY_TYPES
from ..helpers import parse_metadata_from_html_comment
from ..models import (
    CodeBlock,
    Formatting,
    GeometryBlock,
    Heading,
    HtmlBlock,
    Image,
    Link,
    List,
    Node,
    Paragraph,
    Text,
    geometry_to_dict,
)

logger = logging.getLogger(__name__)


class JsonRenderer:
    """Render document nodes to a JSON string."""

    def render(self, nodes: list[Node], as_dict: bool = False) -> str | dict:
        return self._to_json(nodes, as_dict)

    def _to_json(self, nodes: list[Node], as_dict: bool) -> str | dict:
        """
        Render nodes, then apply field mapping and
        extra fields from metadata.
        """
        json_dict = self._render_json(nodes)
        formatted_json_dict = self._map_fields_and_add_extra_fields(json_dict)
        if as_dict:
            return formatted_json_dict
        return json.dumps(formatted_json_dict)

    def _map_fields_and_add_extra_fields(self, data: object) -> object:
        if not isinstance(data, dict):
            return data
        if _is_geometry(data):
            # A geometry is data, not document structure: never rename its members.
            return data

        # Extract metadata up front so mapping applies to *all* sibling
        # keys, regardless of where "_metadata" sits in the dict
        metadata = data.get(_METADATA_KEY) or {}
        extra_fields = metadata.get(_EXTRA_FIELDS) or {}
        field_mapping = metadata.get(_FIELD_MAPPING) or {}
        if not isinstance(field_mapping, dict):
            raise ValueError(f"{_FIELD_MAPPING} must be an object, got {type(field_mapping).__name__}")

        result: dict = {}

        # Merge extras first so they go before real (mapped) content.
        # A list of names (the GeoJSON form) carries no values of its own.
        if isinstance(extra_fields, dict):
            result.update(extra_fields)

        for key, value in data.items():
            if key == _METADATA_KEY:
                continue
            result[field_mapping.get(key, key)] = self._map_fields_and_add_extra_fields(value)

        return result

    def _render_json(self, nodes: list[Node]) -> dict:
        """Convert a node list to a nested dict keyed by heading text.

        Example input:

            # Header 3
            Some text
            ## Header 4
            Content under header 1

        Content that sits before the first heading has no key to hang from and
        is reported instead of being dropped without a word.
        """

        result: dict = {}
        i = 0

        while i < len(nodes):
            node = nodes[i]
            if not isinstance(node, Heading):
                if isinstance(node, (Paragraph, List, CodeBlock, GeometryBlock)):
                    logger.warning(
                        "Content before the first heading is not part of any section: %r",
                        self._preview(node),
                    )
                i += 1
                continue

            # Key is a property name
            key = self._render_paragraph(node.children)

            # Collect everything until the next heading of same/down level
            j = i + 1
            while j < len(nodes):
                next_node = nodes[j]
                if isinstance(next_node, Heading) and next_node.level <= node.level:
                    # Found next same/up level
                    break
                j += 1

            # Current level section content
            section = nodes[i + 1:j]
            section_value: dict = {}

            # Pull a metadata HTML comment from the section head, if present
            # (only when it's not the entire section. Otherwise, it's the content)
            if len(section) > 1:
                first_section_node = section[0]
                if isinstance(first_section_node, HtmlBlock):
                    section_value[_METADATA_KEY] = parse_metadata_from_html_comment(first_section_node.raw)
                    section = section[1:]

            if any(isinstance(_node, Heading) for _node in section):
                # Go deeper if there is Heading
                # Note: We assume that next node is Header, otherwise
                # we lose data
                section_value.update(self._render_json(section))
                result[key] = section_value
            else:
                result[key] = self._render_section(section)

            i = j
        return result

    def _render_section(self, nodes: list[Node]) -> str | list:
        """Render a section's content: a string, or a list when it holds a list."""
        values: list = []
        for node in nodes:
            if isinstance(node, List):
                values.append(self._render_list_block(node.children))
            elif isinstance(node, Paragraph):
                values.append(self._render_paragraph(node.children))
            elif isinstance(node, CodeBlock):
                values.append(node.raw)
            elif isinstance(node, GeometryBlock):
                values.append(self._render_geometry(node))
            elif isinstance(node, HtmlBlock):
                values.append(node.raw)
            else:
                logger.warning("Dropping a %s node from a section value", node.NODE_TYPE)

        if not values:
            return ""
        if len(values) == 1:
            return values[0]
        if all(isinstance(value, str) for value in values):
            return "\n\n".join(values)
        return values

    @staticmethod
    def _render_geometry(node: GeometryBlock) -> object:
        if node.error:
            logger.warning("Keeping the text of an invalid geometry block: %s", node.error)
            return node.raw
        return geometry_to_dict(node.geometry) if node.geometry is not None else None

    def _render_list_block(self, nodes: list[Node]) -> list:
        """Convert list items to resource dicts or plain strings."""
        result: list = []
        for node in nodes:
            if not node.children:
                continue
            if len(node.children) == 1:
                result.append(self._render_resource(node.children[0]))
            else:
                paragraphs = [
                    child for child in node.children if isinstance(child, Paragraph)
                ]
                if paragraphs:
                    result.append(self._render_paragraph(paragraphs[0].children))
                else:
                    logger.warning("List item has no text, only nested blocks")
        return [item for item in result if item is not None]

    def _render_resource(self, node: Node) -> dict | str | None:
        """Convert a Link/Image/Text/Paragraph node"""
        if isinstance(node, Link):
            return {
                "url": node.url,
                "title": node.title
            }
        elif isinstance(node, Image):
            return {
                "url": node.url,
                "title": node.title,
                "alt": node.alt
            }
        elif isinstance(node, Text):
            return node.raw
        elif isinstance(node, Paragraph):
            return self._render_paragraph(node.children)

        return None

    def _render_paragraph(self, nodes: list[Node]) -> str:
        """Flatten inline nodes to plain text (keeps links/images, drops other formatting)."""
        result: list[str] = []
        for node in nodes:
            if isinstance(node, Text):
                result.append(node.raw)
            elif isinstance(node, Formatting):
                result.append(self._render_paragraph(node.children))
            elif isinstance(node, Link):
                title = f'"{node.title}"' if node.title else ""
                result.append(f"[{title}]({node.url})")
            elif isinstance(node, Image):
                # Standard Markdown: ![alt](url "title")
                title = f' "{node.title}"' if node.title else ""
                result.append(f"![{node.alt}]({node.url}{title})")
            elif node.children:
                result.append(self._render_paragraph(node.children))
        return "".join(result)

    @staticmethod
    def _preview(node: Node) -> str:
        if isinstance(node, Paragraph):
            text = "".join(child.raw for child in node.children if isinstance(child, Text))
            return text[:60]
        return node.NODE_TYPE


def _is_geometry(value: dict) -> bool:
    return (
        value.get("type") in GEOMETRY_TYPES
        and ("coordinates" in value or "geometries" in value)
    )
