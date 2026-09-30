import json

from ..helpers import parse_metadata_from_html_comment
from ..models import Node, Heading, Paragraph, Text, List, Link, Image, ListItem, HtmlBlock
from ..constants import _METADATA_KEY, _FIELD_MAPPING, _EXTRA_FIELDS


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

    def _map_fields_and_add_extra_fields(self, data: dict) -> dict:
        if not isinstance(data, dict):
            return data

        # Extract metadata up front so mapping applies to *all* sibling
        # keys, regardless of where "_metadata" sits in the dict
        metadata = data.get(_METADATA_KEY) or {}
        extra_fields = metadata.get(_EXTRA_FIELDS) or {}
        field_mapping = metadata.get(_FIELD_MAPPING) or {}

        result: dict = {}

        # Merge extras first so they go before real (mapped) content
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

        Note: Some text will be lost in the current implementation
        """

        result: dict = {}
        i = 0

        while i < len(nodes):
            node = nodes[i]
            if not isinstance(node, Heading):
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
                values = self._render_section(section)
                if not values:
                    result[key] = ""
                elif len(values) == 1:
                    result[key] = values[0]
                else:
                    result[key] = values

            i = j
        return result

    def _render_section(self, nodes: list[Node]) -> list | str:
        """Render a section's content."""
        if len(nodes) == 1:
            node = nodes[0]
            if isinstance(node, List):
                return self._render_list_block(node.children)
            elif isinstance(node, HtmlBlock):
                return node.raw

        # General case: paragraphs and inline lists joined by blank lines
        result: list[str] = []
        for node in nodes:
            if isinstance(node, List):
                result.append(self._render_inline_list(node.children, ordered=node.ordered))
            elif isinstance(node, Paragraph):
                result.append(self._render_paragraph(node.children))
        return "\n\n".join(result)

    def _render_list_block(self, nodes: list[Node]) -> list:
        """Convert list items to resource dicts or plain strings."""
        result: list = []
        for node in nodes:
            if not node.children:
                continue
            result.append(self._render_resource(node.children[0]))
        return result

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
            return self._render_resource(node.children[0])

        return None

    def _render_inline_list(
            self,
            nodes: list[ListItem],
            ordered: bool = False,
            indent: int = 0
    ) -> str:
        """Render list items as Markdown bullets / numbered lines."""
        result: list[str] = []
        for i, node in enumerate(nodes):
            marker = f"{i + 1}. " if ordered else "- "
            pad = " " * indent
            for child in node.children:
                content = []
                if isinstance(child, Paragraph):
                    content.append(self._render_paragraph(child.children))
                result.append(pad + marker + "\n".join(content))
        return "\n".join(result)


    def _render_paragraph(self, nodes: list[Node]) -> str:
        """Flatten inline nodes to plain text (keeps links/images, drops other formatting)."""
        result: list[str] = []
        for node in nodes:
            if isinstance(node, Text):
                result.append(node.raw)
            if isinstance(node, Link):
                title = f'"{node.title}"' if node.title else ""
                result.append(f"[{title}]({node.url})")
            elif isinstance(node, Image):
                # Standard Markdown: ![alt](url "title")
                title = f' "{node.title}"' if node.title else ""
                result.append(f"![{node.alt}]({node.url}{title})")
            else:
                result.append(self._render_paragraph(getattr(node, "children", [])))
        return "".join(result)
