import geojson

from ..models import Node, Heading, Paragraph, CodeBlock, Text, Link, Image, List, ListItem, GeometryBlock, \
    HtmlBlock, ImageList, TextBlock


class MarkdownRenderer:
    """Render document nodes back to Markdown text."""

    def render(
            self,
            nodes: list[Node],
            *,
            as_dict: bool = False,
            auto_contents: bool = False,
            contents_title: str = "Contents"
    ) -> str:
        if as_dict:
            raise NotImplementedError(
                f"{type(self).__name__} does not support as_dict=True; it renders text only"
            )
        return self._to_markdown(nodes, auto_contents, contents_title)

    def _to_markdown(self, nodes: list[Node], auto_contents: bool, contents_title: str) -> str:
        """Convert each block node to its Markdown form, joined by blank lines."""

        contents_items: list[str] = []
        contents_start: int = -1
        blocks: list[str] = []
        for i, node in enumerate(nodes):
            if isinstance(node, Heading):
                inline = self._render_inline(node.children)
                if auto_contents and node.level == 2:
                    if not contents_items:
                        contents_start = i
                        contents_items.append(f"### {contents_title}")
                    contents_items.append(f"- {header_to_link(inline)}")
                blocks.append("#" * node.level + " " + inline)
            elif isinstance(node, Paragraph):
                blocks.append(self._render_inline(node.children))
            elif isinstance(node, List):
                blocks.append(self._render_list(node.children, ordered=node.ordered))
            elif isinstance(node, TextBlock):
                blocks.append(self._render_text_block(node))
            elif isinstance(node, ImageList):
                blocks.append(self._render_image_list(node.children))
            elif isinstance(node, CodeBlock):
                language = node.language or ""
                blocks.append(f"```{language}\n{node.raw}\n```")
            elif isinstance(node, HtmlBlock):
                blocks.append(f"{node.raw}")
            elif isinstance(node, GeometryBlock):
                blocks.append(self._render_geometry_block(node))
            else:
                raise ValueError(f"No such block node: {node.NODE_TYPE}")

        if auto_contents and contents_items:
            blocks.insert(contents_start, "\n".join(contents_items))

        return "\n\n".join(blocks) + "\n"

    def _render_geometry_block(self, node: GeometryBlock) -> str:
        return f"```json\n{geojson.dumps(node.geometry)}\n```"

    def _render_list(
            self,
            nodes: list[Node],
            ordered: bool = False,
            indent: int = 0
    ) -> str:
        """Render list items as Markdown bullets or numbered entries."""
        lines: list[str] = []
        pad = " " * indent

        for i, item in enumerate(nodes):
            if (len(item.children) != 1
                    or not isinstance(item, ListItem)
                    or not isinstance(item.children[0], TextBlock)
            ):
                continue
            marker = f"{i + 1}. " if ordered else "- "
            text_block: TextBlock = item.children[0]
            body = self._render_text_block(text_block).strip()
            body_lines = body.splitlines() or [""]

            # First line carries the marker; continuation lines are indented
            # to line up with the item's text
            lines.append(pad + marker + body_lines[0])
            continuation = " " * len(marker)
            for line in body_lines[1:]:
                lines.append(pad + continuation + line)

        return "\n".join(lines)

    def _render_image_list(self, nodes: list[Node]) -> str:
        return self._render_list(nodes, ordered=False, indent=0)

    def _render_inline(self, nodes: list[Node]) -> str:
        """Flatten inline nodes (Text/Link/Image) to a single string."""

        result: list[str] = []
        for node in nodes:
            if isinstance(node, Text):
                result.append(node.raw)
            elif isinstance(node, Link):
                title = f'"{node.title}"' if node.title else ""
                result.append(f"[{title}]({node.url})")
            elif isinstance(node, Image):
                # Standard Markdown: ![alt](url "title")
                title = f' "{node.title}"' if node.title else ""
                result.append(f"![{node.alt}]({node.url}{title})")
            else:
                raise ValueError(f"No such inline node: {node.NODE_TYPE}")
        return "".join(result)

    def _render_text_block(self, node: TextBlock) -> str:
        return self._render_inline(node.children)


def to_link_anchor(header: str) -> str:
    return header.strip().replace(" ", "-")


def header_to_link(header: str) -> str:
    return f"[{header}](#{to_link_anchor(header)})"


def heading_to_text(heading: Heading) -> str:
    def node_to_text(node: Node):
        result = []
        if isinstance(node, Text):
            return [node.raw.strip()]
        elif len(node.children) > 0:
            for child in node.children:
                result.extend(node_to_text(child))
        return result

    text_list = node_to_text(heading)
    return " ".join(text_list)
